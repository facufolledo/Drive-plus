import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICACIÓN ZONA C - 5TA CATEGORÍA - TORNEO 46")
print("=" * 80)

# Ver todas las parejas de Zona C
cur.execute("""
    SELECT DISTINCT
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as jugador1,
        pu2.nombre || ' ' || pu2.apellido as jugador2,
        tp.disponibilidad_horaria
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    JOIN partidos p ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
    JOIN torneo_zonas z ON p.zona_id = z.id
    WHERE p.id_torneo = 46
    AND z.nombre = 'Zona C'
    AND z.categoria_id = (SELECT id FROM torneo_categorias WHERE id_torneo = 46 AND nombre = '5ta')
    ORDER BY tp.id
""")

parejas = cur.fetchall()

print("\n📋 PAREJAS EN ZONA C:")
for p in parejas:
    print(f"\n  Pareja {p['id']}: {p['jugador1']} / {p['jugador2']}")
    if p['disponibilidad_horaria']:
        print("    Restricciones:")
        for r in p['disponibilidad_horaria']:
            dias = ', '.join(r.get('dias', []))
            print(f"      NO disponible {dias} de {r.get('horaInicio')} a {r.get('horaFin')}")

# Ver todos los partidos de Zona C
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        pu1.nombre || ' ' || pu1.apellido as p1_j1,
        pu2.nombre || ' ' || pu2.apellido as p1_j2,
        pu3.nombre || ' ' || pu3.apellido as p2_j1,
        pu4.nombre || ' ' || pu4.apellido as p2_j2,
        tp1.jugador1_id as j1_p1,
        tp1.jugador2_id as j2_p1,
        tp2.jugador1_id as j1_p2,
        tp2.jugador2_id as j2_p2
    FROM partidos p
    JOIN torneo_zonas z ON p.zona_id = z.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46
    AND z.nombre = 'Zona C'
    AND z.categoria_id = (SELECT id FROM torneo_categorias WHERE id_torneo = 46 AND nombre = '5ta')
    ORDER BY p.fecha_hora
""")

partidos = cur.fetchall()

print("\n" + "=" * 80)
print("PARTIDOS EN ZONA C:")
print("=" * 80)

for p in partidos:
    dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
    print(f"\nPartido {p['id_partido']}: {dia} {p['fecha_hora'].strftime('%H:%M')}")
    print(f"  {p['p1_j1']} / {p['p1_j2']} vs {p['p2_j1']} / {p['p2_j2']}")

# Verificar específicamente Luciano Paez
print("\n" + "=" * 80)
print("ANÁLISIS ESPECÍFICO: LUCIANO PAEZ")
print("=" * 80)

cur.execute("""
    SELECT 
        pu.id_usuario,
        pu.nombre || ' ' || pu.apellido as nombre_completo
    FROM perfil_usuarios pu
    WHERE LOWER(pu.nombre || ' ' || pu.apellido) LIKE '%luciano%paez%'
""")

luciano = cur.fetchone()

if luciano:
    print(f"\n✅ Encontrado: {luciano['nombre_completo']} (ID: {luciano['id_usuario']})")
    
    # Ver todos los partidos de Luciano
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            tc.nombre as categoria,
            z.nombre as zona,
            pu1.nombre || ' ' || pu1.apellido as p1_j1,
            pu2.nombre || ' ' || pu2.apellido as p1_j2,
            pu3.nombre || ' ' || pu3.apellido as p2_j1,
            pu4.nombre || ' ' || pu4.apellido as p2_j2
        FROM partidos p
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id_torneo = 46
        AND (tp1.jugador1_id = %s OR tp1.jugador2_id = %s OR tp2.jugador1_id = %s OR tp2.jugador2_id = %s)
        AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora
    """, (luciano['id_usuario'], luciano['id_usuario'], luciano['id_usuario'], luciano['id_usuario']))
    
    partidos_luciano = cur.fetchall()
    
    print(f"\n📅 PARTIDOS DE LUCIANO PAEZ ({len(partidos_luciano)} partidos):")
    
    for i, p in enumerate(partidos_luciano):
        dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
        print(f"\n  {i+1}. Partido {p['id_partido']}: {dia} {p['fecha_hora'].strftime('%H:%M')} - {p['categoria']} - {p['zona']}")
        print(f"     {p['p1_j1']} / {p['p1_j2']} vs {p['p2_j1']} / {p['p2_j2']}")
        
        # Calcular tiempo hasta el siguiente partido
        if i < len(partidos_luciano) - 1:
            siguiente = partidos_luciano[i + 1]
            diff_minutos = (siguiente['fecha_hora'] - p['fecha_hora']).total_seconds() / 60
            print(f"     ⏱️  Tiempo hasta siguiente partido: {int(diff_minutos)} minutos")
            
            if diff_minutos < 180:
                print(f"     ⚠️  MENOS DE 3 HORAS (aceptable en zona de 3 parejas)")
            else:
                print(f"     ✅ Más de 3 horas de descanso")

print("\n" + "=" * 80)
print("✅ VERIFICACIÓN COMPLETADA")
print("=" * 80)

cur.close()
conn.close()
