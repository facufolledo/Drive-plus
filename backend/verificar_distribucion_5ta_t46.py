import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

# Ver zonas y parejas
cur.execute("""
    SELECT 
        z.id as zona_id,
        z.nombre as zona_nombre,
        COUNT(p.id_partido) as partidos
    FROM torneo_zonas z
    LEFT JOIN partidos p ON z.id = p.zona_id
    WHERE z.torneo_id = 46 AND z.categoria_id = 127
    GROUP BY z.id, z.nombre
    ORDER BY z.numero_orden
""")

print("Distribución actual de zonas y partidos:")
for zona in cur.fetchall():
    print(f"  {zona['zona_nombre']}: {zona['partidos']} partidos")

# Ver todas las parejas
cur.execute("""
    SELECT 
        tp.id,
        p1.nombre || ' ' || p1.apellido as jugador1,
        p2.nombre || ' ' || p2.apellido as jugador2
    FROM torneos_parejas tp
    JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
    JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
    WHERE tp.torneo_id = 46 AND tp.categoria_id = 127
    ORDER BY tp.id
""")

print("\nTodas las parejas inscritas:")
parejas = cur.fetchall()
for i, p in enumerate(parejas, 1):
    print(f"  {i}. Pareja {p['id']}: {p['jugador1']} / {p['jugador2']}")

print(f"\nTotal: {len(parejas)} parejas")
print(f"Distribución ideal: 3 zonas de 3 parejas + 1 zona de 2 parejas = 11 parejas")
print(f"O: 2 zonas de 3 parejas + 4 zonas de 2 parejas = 14 parejas ✓")

cur.close()
conn.close()
