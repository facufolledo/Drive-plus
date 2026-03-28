import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

# Obtener categoria_id de 7ma
cur.execute("""
    SELECT id FROM torneo_categorias 
    WHERE torneo_id = 46 AND nombre = '7ma'
""")
categoria_id = cur.fetchone()['id']

# Ver todas las parejas de 7ma
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
print(f"Total parejas inscritas en 7ma: {len(parejas)}\n")

# Ver en qué zona está cada pareja (según partidos)
for pareja in parejas:
    cur.execute("""
        SELECT DISTINCT z.nombre as zona
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        WHERE p.id_torneo = 46 
        AND p.categoria_id = %s
        AND (p.pareja1_id = %s OR p.pareja2_id = %s)
    """, (categoria_id, pareja['id'], pareja['id']))
    
    zona = cur.fetchone()
    zona_nombre = zona['zona'] if zona else "❌ SIN ZONA"
    print(f"Pareja {pareja['id']}: {pareja['jugador1']} / {pareja['jugador2']} → {zona_nombre}")

# Contar parejas por zona
cur.execute("""
    SELECT 
        z.nombre as zona,
        COUNT(DISTINCT CASE WHEN p.pareja1_id IS NOT NULL THEN p.pareja1_id END) +
        COUNT(DISTINCT CASE WHEN p.pareja2_id IS NOT NULL THEN p.pareja2_id END) as parejas_count,
        COUNT(p.id_partido) as partidos_count
    FROM torneo_zonas z
    LEFT JOIN partidos p ON z.id = p.zona_id AND p.id_torneo = 46 AND p.categoria_id = %s
    WHERE z.torneo_id = 46 AND z.categoria_id = %s
    GROUP BY z.id, z.nombre, z.numero_orden
    ORDER BY z.numero_orden
""", (categoria_id, categoria_id))

print("\n\nResumen por zona:")
for zona in cur.fetchall():
    print(f"  {zona['zona']}: {zona['parejas_count']} parejas, {zona['partidos_count']} partidos")

cur.close()
conn.close()
