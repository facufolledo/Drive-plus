import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

def obtener_nombres_jugadores(jugador_ids):
    """Obtiene nombres completos de jugadores"""
    if not jugador_ids:
        return []
    
    cur.execute("""
        SELECT id_usuario, nombre, apellido
        FROM perfil_usuarios
        WHERE id_usuario = ANY(%s)
    """, (list(jugador_ids),))
    
    jugadores = {}
    for j in cur.fetchall():
        jugadores[j['id_usuario']] = f"{j['nombre']} {j['apellido']}"
    
    return [jugadores.get(jid, f"ID:{jid}") for jid in jugador_ids]

def obtener_nombres_pareja(pareja_id):
    """Obtiene nombres de ambos jugadores de una pareja"""
    cur.execute("""
        SELECT 
            tp.id,
            pu1.nombre || ' ' || pu1.apellido as jugador1,
            pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneos_parejas tp
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id = %s
    """, (pareja_id,))
    
    pareja = cur.fetchone()
    if pareja:
        return f"{pareja['jugador1']} / {pareja['jugador2']}"
    return f"Pareja {pareja_id}"

print("=" * 100)
print("REPORTE DETALLADO DE PROBLEMAS - TORNEO 46")
print("=" * 100)

# Obtener todos los partidos con horarios
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        tc.nombre as categoria,
        z.nombre as zona,
        p.pareja1_id,
        p.pareja2_id,
        tp1.jugador1_id as j1_p1,
        tp1.jugador2_id as j2_p1,
        tp2.jugador1_id as j1_p2,
        tp2.jugador2_id as j2_p2
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    JOIN torneo_zonas z ON p.zona_id = z.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    WHERE p.id_torneo = 46 
    AND tc.nombre IN ('7ma', '5ta')
    AND p.fecha_hora IS NOT NULL
    ORDER BY p.fecha_hora, p.id_partido
""")

partidos = cur.fetchall()

# 1. SOLAPAMIENTOS (menos de 3 horas entre partidos del mismo jugador)
print("\n" + "=" * 100)
print("SOLAPAMIENTOS (Jugadores con menos de 3 horas de descanso)")
print("=" * 100)

TIEMPO_DESCANSO_MINIMO = 180
solapamientos_encontrados = []

for i, p1 in enumerate(partidos):
    jugadores_p1 = {p1['j1_p1'], p1['j2_p1'], p1['j1_p2'], p1['j2_p2']}
    
    for p2 in partidos[i+1:]:
        jugadores_p2 = {p2['j1_p1'], p2['j2_p1'], p2['j1_p2'], p2['j2_p2']}
        jugadores_comunes = jugadores_p1 & jugadores_p2
        
        if jugadores_comunes:
            diff_minutos = abs((p2['fecha_hora'] - p1['fecha_hora']).total_seconds() / 60)
            
            if diff_minutos < TIEMPO_DESCANSO_MINIMO:
                nombres_comunes = obtener_nombres_jugadores(jugadores_comunes)
                pareja1_nombres = obtener_nombres_pareja(p1['pareja1_id'])
                pareja2_nombres = obtener_nombres_pareja(p1['pareja2_id'])
                pareja3_nombres = obtener_nombres_pareja(p2['pareja1_id'])
                pareja4_nombres = obtener_nombres_pareja(p2['pareja2_id'])
                
                solapamientos_encontrados.append({
                    'partido1': p1['id_partido'],
                    'partido2': p2['id_partido'],
                    'categoria1': p1['categoria'],
                    'categoria2': p2['categoria'],
                    'zona1': p1['zona'],
                    'zona2': p2['zona'],
                    'fecha1': p1['fecha_hora'].strftime('%Y-%m-%d %H:%M'),
                    'fecha2': p2['fecha_hora'].strftime('%Y-%m-%d %H:%M'),
                    'pareja1': pareja1_nombres,
                    'pareja2': pareja2_nombres,
                    'pareja3': pareja3_nombres,
                    'pareja4': pareja4_nombres,
                    'jugadores_comunes': nombres_comunes,
                    'diff_minutos': int(diff_minutos)
                })

if solapamientos_encontrados:
    for idx, s in enumerate(solapamientos_encontrados, 1):
        print(f"\n{idx}. SOLAPAMIENTO:")
        print(f"   Partido {s['partido1']}: {s['categoria1']} - {s['zona1']} - {s['fecha1']}")
        print(f"   Parejas: {s['pareja1']} vs {s['pareja2']}")
        print(f"   vs")
        print(f"   Partido {s['partido2']}: {s['categoria2']} - {s['zona2']} - {s['fecha2']}")
        print(f"   Parejas: {s['pareja3']} vs {s['pareja4']}")
        print(f"   Jugadores afectados: {', '.join(s['jugadores_comunes'])}")
        print(f"   Tiempo entre partidos: {s['diff_minutos']} minutos (mínimo: 180)")
else:
    print("\n✅ No hay solapamientos")

# 2. VIOLACIONES DE RESTRICCIONES
print("\n" + "=" * 100)
print("VIOLACIONES DE RESTRICCIONES")
print("=" * 100)

violaciones = []

for partido in partidos:
    # Obtener restricciones de ambas parejas
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
                            'categoria': partido['categoria'],
                            'zona': partido['zona'],
                            'fecha': fecha_partido.strftime('%Y-%m-%d %H:%M'),
                            'pareja': f"{pareja_data['jugador1']} / {pareja_data['jugador2']}",
                            'restriccion': f"No disponible {dia_es} de {hora_inicio} a {hora_fin}"
                        })

if violaciones:
    for idx, v in enumerate(violaciones, 1):
        print(f"\n{idx}. VIOLACIÓN DE RESTRICCIÓN:")
        print(f"   Partido {v['partido']}: {v['categoria']} - {v['zona']} - {v['fecha']}")
        print(f"   Pareja afectada: {v['pareja']}")
        print(f"   Problema: {v['restriccion']}")
else:
    print("\n✅ No hay violaciones de restricciones")

print("\n" + "=" * 100)
print(f"RESUMEN: {len(solapamientos_encontrados)} solapamientos, {len(violaciones)} violaciones")
print("=" * 100)

cur.close()
conn.close()
