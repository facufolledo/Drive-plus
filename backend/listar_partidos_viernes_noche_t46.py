import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, time

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("PARTIDOS VIERNES 20:30 - 00:00 - TORNEO 46")
print("=" * 80)

# Buscar partidos del viernes entre 20:30 y 00:00
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tc.nombre as categoria,
        tz.nombre as zona,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46
    AND DATE(p.fecha_hora) = '2026-03-27'
    AND EXTRACT(HOUR FROM p.fecha_hora) * 60 + EXTRACT(MINUTE FROM p.fecha_hora) >= 20 * 60 + 30
    ORDER BY p.fecha_hora, p.cancha_id
""")

partidos = cur.fetchall()

print(f"\n📊 Total partidos: {len(partidos)}")
print("\n" + "-" * 80)

# Agrupar por horario
horarios = {}
for p in partidos:
    hora = p['fecha_hora'].strftime('%H:%M')
    if hora not in horarios:
        horarios[hora] = []
    horarios[hora].append(p)

# Mostrar por horario
for hora in sorted(horarios.keys()):
    print(f"\n🕐 {hora}")
    print("-" * 80)
    
    for p in horarios[hora]:
        print(f"\n  Partido {p['id_partido']} - Cancha {p['cancha_id']}")
        print(f"  {p['categoria']} - {p['zona']}")
        print(f"  {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")

print("\n" + "=" * 80)
print("RESUMEN POR CANCHA")
print("=" * 80)

cur.execute("""
    SELECT 
        p.cancha_id,
        COUNT(*) as total_partidos,
        MIN(p.fecha_hora) as primer_partido,
        MAX(p.fecha_hora) as ultimo_partido
    FROM partidos p
    WHERE p.id_torneo = 46
    AND DATE(p.fecha_hora) = '2026-03-27'
    AND EXTRACT(HOUR FROM p.fecha_hora) * 60 + EXTRACT(MINUTE FROM p.fecha_hora) >= 20 * 60 + 30
    GROUP BY p.cancha_id
    ORDER BY p.cancha_id
""")

resumen = cur.fetchall()

for r in resumen:
    print(f"\nCancha {r['cancha_id']}: {r['total_partidos']} partidos")
    print(f"  Desde: {r['primer_partido'].strftime('%H:%M')}")
    print(f"  Hasta: {r['ultimo_partido'].strftime('%H:%M')}")

cur.close()
conn.close()
