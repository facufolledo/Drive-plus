import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

# Buscar partidos 1075 y 1076
cur.execute("""
    SELECT 
        p.id_partido,
        p.id_torneo,
        p.categoria_id,
        p.zona_id,
        z.nombre as zona_nombre,
        p.pareja1_id,
        p.pareja2_id,
        p.fecha_hora
    FROM partidos p
    LEFT JOIN torneo_zonas z ON p.zona_id = z.id
    WHERE p.id_partido IN (1075, 1076)
""")

partidos = cur.fetchall()

if partidos:
    print("Partidos 1075 y 1076 encontrados:")
    for p in partidos:
        print(f"\nPartido {p['id_partido']}:")
        print(f"  Torneo: {p['id_torneo']}")
        print(f"  Categoría: {p['categoria_id']}")
        print(f"  Zona: {p['zona_nombre']} (ID: {p['zona_id']})")
        print(f"  Parejas: {p['pareja1_id']} vs {p['pareja2_id']}")
        print(f"  Fecha: {p['fecha_hora']}")
else:
    print("❌ Partidos 1075 y 1076 NO encontrados")
    
    # Ver cuál es el último partido creado
    cur.execute("""
        SELECT MAX(id_partido) as ultimo_id
        FROM partidos
        WHERE id_torneo = 46
    """)
    ultimo = cur.fetchone()
    print(f"\nÚltimo partido del torneo 46: {ultimo['ultimo_id']}")

cur.close()
conn.close()
