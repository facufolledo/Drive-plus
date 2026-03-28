import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

# Ver categorías usadas en torneo 46
cur.execute("""
    SELECT DISTINCT
        tz.categoria_id,
        c.nombre as categoria_nombre,
        COUNT(tz.id) as zonas
    FROM torneo_zonas tz
    LEFT JOIN categorias c ON tz.categoria_id = c.id_categoria
    WHERE tz.torneo_id = 46
    GROUP BY tz.categoria_id, c.nombre
    ORDER BY tz.categoria_id
""")

cats = cur.fetchall()

print("Categorías en Torneo 46:")
for cat in cats:
    print(f"  ID {cat['categoria_id']}: {cat['categoria_nombre']} - {cat['zonas']} zonas")

cur.close()
conn.close()
