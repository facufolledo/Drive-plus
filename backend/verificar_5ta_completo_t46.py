import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICACIÓN COMPLETA DE 5TA - TORNEO 46")
print("=" * 80)

# 1. Obtener categoría 5ta
cur.execute("SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '5ta'")
categoria = cur.fetchone()

if not categoria:
    print("❌ No se encontró categoría 5ta")
    cur.close()
    conn.close()
    exit()

categoria_id = categoria['id']

# 2. Parejas inscritas
cur.execute("""
    SELECT 
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as jugador1,
        pu2.nombre || ' ' || pu2.apellido as jugador2
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tp.torneo_id = 46 AND tp.categoria_id = %s
    ORDER BY tp.id
""", (categoria_id,))

parejas = cur.fetchall()
print(f"\n📋 PAREJAS INSCRITAS: {len(parejas)}")
for p in parejas:
    print(f"  Pareja {p['id']}: {p['jugador1']} / {p['jugador2']}")

# 3. Zonas creadas
cur.execute("""
    SELECT id, nombre, numero_orden
    FROM torneo_zonas
    WHERE torneo_id = 46 AND categoria_id = %s
    ORDER BY numero_orden
""", (categoria_id,))

zonas = cur.fetchall()
print(f"\n🏆 ZONAS CREADAS: {len(zonas)}")
for z in zonas:
    print(f"  {z['nombre']} (ID: {z['id']})")

# 4. Partidos generados
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        z.nombre as zona,
        tp1.id as pareja1_id,
        tp2.id as pareja2_id,
        pu1.nombre || ' ' || pu1.apellido as p1_j1,
        pu2.nombre || ' ' || pu2.apellido as p1_j2,
        pu3.nombre || ' ' || pu3.apellido as p2_j1,
        pu4.nombre || ' ' || pu4.apellido as p2_j2
    FROM partidos p
    JOIN torneo_zonas z ON p.zona_id = z.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46 AND p.categoria_id = %s
    ORDER BY z.nombre, p.fecha_hora NULLS LAST
""", (categoria_id,))

partidos = cur.fetchall()
print(f"\n⚽ PARTIDOS GENERADOS: {len(partidos)}")

# Agrupar por zona
partidos_por_zona = {}
for p in partidos:
    zona = p['zona']
    if zona not in partidos_por_zona:
        partidos_por_zona[zona] = []
    partidos_por_zona[zona].append(p)

for zona, partidos_zona in sorted(partidos_por_zona.items()):
    print(f"\n  {zona}:")
    for p in partidos_zona:
        horario = p['fecha_hora'].strftime('%Y-%m-%d %H:%M') if p['fecha_hora'] else 'SIN HORARIO'
        print(f"    Partido {p['id_partido']}: {horario}")
        print(f"      P{p['pareja1_id']}: {p['p1_j1']} / {p['p1_j2']}")
        print(f"      vs")
        print(f"      P{p['pareja2_id']}: {p['p2_j1']} / {p['p2_j2']}")

# 5. Partidos con y sin horario
con_horario = sum(1 for p in partidos if p['fecha_hora'] is not None)
sin_horario = len(partidos) - con_horario

print(f"\n📊 RESUMEN:")
print(f"  Total partidos: {len(partidos)}")
print(f"  Con horario: {con_horario}")
print(f"  Sin horario: {sin_horario}")

# 6. Verificar restricciones en partidos con horario
if con_horario > 0:
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE RESTRICCIONES")
    print("=" * 80)
    
    violaciones = []
    
    for partido in partidos:
        if partido['fecha_hora'] is None:
            continue
        
        # Verificar restricciones de ambas parejas
        cur.execute("""
            SELECT 
                tp.id as pareja_id,
                tp.disponibilidad_horaria,
                pu1.nombre || ' ' || pu1.apellido as jugador1,
                pu2.nombre || ' ' || pu2.apellido as jugador2
            FROM torneos_parejas tp
            JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tp.id IN (%s, %s)
        """, (partido['pareja1_id'], partido['pareja2_id']))
        
        parejas_data = cur.fetchall()
        
        for pareja_data in parejas_data:
            if pareja_data['disponibilidad_horaria']:
                restricciones_data = pareja_data['disponibilidad_horaria']
                
                fecha_partido = partido['fecha_hora']
                dia_semana = fecha_partido.strftime('%A').lower()
                dia_map = {
                    'monday': 'lunes', 'tuesday': 'martes', 'wednesday': 'miércoles',
                    'thursday': 'jueves', 'friday': 'viernes', 'saturday': 'sábado', 'sunday': 'domingo'
                }
                dia_es = dia_map.get(dia_semana, dia_semana)
                hora_partido = fecha_partido.strftime('%H:%M')
                
                for restriccion in restricciones_data:
                    if dia_es in restriccion.get('dias', []):
                        hora_inicio = restriccion.get('horaInicio', '00:00')
                        hora_fin = restriccion.get('horaFin', '23:59')
                        
                        if hora_inicio <= hora_partido <= hora_fin:
                            violaciones.append({
                                'partido': partido['id_partido'],
                                'zona': partido['zona'],
                                'fecha': fecha_partido.strftime('%Y-%m-%d %H:%M'),
                                'pareja': f"{pareja_data['jugador1']} / {pareja_data['jugador2']}",
                                'restriccion': f"No disponible {dia_es} de {hora_inicio} a {hora_fin}"
                            })
    
    if violaciones:
        print(f"\n❌ ENCONTRADAS {len(violaciones)} VIOLACIONES:\n")
        for v in violaciones:
            print(f"  Partido {v['partido']} - {v['zona']} - {v['fecha']}")
            print(f"    Pareja: {v['pareja']}")
            print(f"    Problema: {v['restriccion']}\n")
    else:
        print("\n✅ No hay violaciones de restricciones")

# 7. Verificar solapamientos
if con_horario > 1:
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE SOLAPAMIENTOS")
    print("=" * 80)
    
    partidos_con_horario = [p for p in partidos if p['fecha_hora'] is not None]
    solapamientos = []
    
    for i, p1 in enumerate(partidos_con_horario):
        # Obtener IDs de jugadores del partido 1
        cur.execute("""
            SELECT jugador1_id, jugador2_id
            FROM torneos_parejas
            WHERE id IN (%s, %s)
        """, (p1['pareja1_id'], p1['pareja2_id']))
        
        jugadores_p1 = set()
        for row in cur.fetchall():
            jugadores_p1.add(row['jugador1_id'])
            jugadores_p1.add(row['jugador2_id'])
        
        for p2 in partidos_con_horario[i+1:]:
            # Obtener IDs de jugadores del partido 2
            cur.execute("""
                SELECT jugador1_id, jugador2_id
                FROM torneos_parejas
                WHERE id IN (%s, %s)
            """, (p2['pareja1_id'], p2['pareja2_id']))
            
            jugadores_p2 = set()
            for row in cur.fetchall():
                jugadores_p2.add(row['jugador1_id'])
                jugadores_p2.add(row['jugador2_id'])
            
            jugadores_comunes = jugadores_p1 & jugadores_p2
            
            if jugadores_comunes:
                diff_minutos = abs((p2['fecha_hora'] - p1['fecha_hora']).total_seconds() / 60)
                
                if diff_minutos < 180:
                    solapamientos.append({
                        'p1': p1,
                        'p2': p2,
                        'diff': diff_minutos
                    })
    
    if solapamientos:
        print(f"\n⚠️ ENCONTRADOS {len(solapamientos)} SOLAPAMIENTOS:\n")
        for s in solapamientos:
            print(f"  Partido {s['p1']['id_partido']} ({s['p1']['zona']}) - {s['p1']['fecha_hora'].strftime('%H:%M')}")
            print(f"  vs")
            print(f"  Partido {s['p2']['id_partido']} ({s['p2']['zona']}) - {s['p2']['fecha_hora'].strftime('%H:%M')}")
            print(f"  Diferencia: {s['diff']:.0f} minutos\n")
    else:
        print("\n✅ No hay solapamientos")

print("\n" + "=" * 80)
print("VERIFICACIÓN COMPLETADA")
print("=" * 80)

cur.close()
conn.close()
