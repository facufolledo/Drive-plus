import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

# Ver partidos por zona
cur.execute("""
    SELECT 
        z.nombre as zona,
        p.id_partido,
        tp1.id as pareja1_id,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        tp2.id as pareja2_id,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2
    FROM partidos p
    JOIN torneo_zonas z ON p.zona_id = z.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46 AND p.categoria_id = 127
    ORDER BY z.numero_orden, p.id_partido
""")

print("Partidos actuales por zona:")
zona_actual = None
for partido in cur.fetchall():
    if zona_actual != partido['zona']:
        zona_actual = partido['zona']
        print(f"\n{zona_actual}:")
    print(f"  Partido {partido['id_partido']}: P{partido['pareja1_id']} ({partido['j1_p1']}/{partido['j2_p1']}) vs P{partido['pareja2_id']} ({partido['j1_p2']}/{partido['j2_p2']})")

# Contar parejas únicas por zona
cur.execute("""
    SELECT 
        z.nombre as zona,
        COUNT(DISTINCT p.pareja1_id) + COUNT(DISTINCT p.pareja2_id) as parejas_unicas
    FROM partidos p
    JOIN torneo_zonas z ON p.zona_id = z.id
    WHERE p.id_torneo = 46 AND p.categoria_id = 127
    GROUP BY z.id, z.nombre, z.numero_orden
    ORDER BY z.numero_orden
""")

print("\n\nParejas por zona:")
for zona in cur.fetchall():
    print(f"  {zona['zona']}: {zona['parejas_unicas']} parejas")

cur.close()
conn.close()
