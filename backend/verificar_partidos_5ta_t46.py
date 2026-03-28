import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

def conectar_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url.startswith('postgresql+pg8000://'):
        db_url = db_url.replace('postgresql+pg8000://', 'postgresql://')
    return psycopg2.connect(db_url)

conn = conectar_db()
cur = conn.cursor(cursor_factory=RealDictCursor)

# Verificar categoria 5ta
cur.execute("""
    SELECT id, nombre
    FROM torneo_categorias
    WHERE torneo_id = 46 AND nombre = '5ta'
""")

categoria = cur.fetchone()

if not categoria:
    print("\nNo se encontro la categoria 5ta en el torneo 46")
    cur.close()
    conn.close()
    exit()

print(f"\nCategoria 5ta: ID {categoria['id']}")

# Contar parejas inscritas
cur.execute("""
    SELECT COUNT(*) as total
    FROM torneos_parejas
    WHERE torneo_id = 46 AND categoria_id = %s
""", (categoria['id'],))

parejas = cur.fetchone()['total']
print(f"Parejas inscritas: {parejas}")

# Contar partidos generados
cur.execute("""
    SELECT COUNT(*) as total
    FROM partidos
    WHERE id_torneo = 46 AND categoria_id = %s
""", (categoria['id'],))

partidos = cur.fetchone()['total']
print(f"Partidos generados: {partidos}")

if partidos > 0:
    print("\nDetalle de partidos:")
    cur.execute("""
        SELECT 
            fase,
            COUNT(*) as total,
            COUNT(CASE WHEN fecha_hora IS NOT NULL THEN 1 END) as con_horario
        FROM partidos
        WHERE id_torneo = 46 AND categoria_id = %s
        GROUP BY fase
        ORDER BY fase
    """, (categoria['id'],))
    
    for row in cur.fetchall():
        print(f"  {row['fase']}: {row['total']} partidos ({row['con_horario']} con horario)")
else:
    print("\nNo hay partidos generados para 5ta")

cur.close()
conn.close()
