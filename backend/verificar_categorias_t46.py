"""Verificar categorías del torneo 46"""

import os
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

# Listar categorías del torneo 46
cur.execute("""
    SELECT id, nombre, genero
    FROM torneo_categorias
    WHERE torneo_id = 46
    ORDER BY id
""")

categorias = cur.fetchall()

print("\n=== CATEGORÍAS TORNEO 46 ===\n")
for cat in categorias:
    print(f"ID: {cat['id']} | Nombre: {cat['nombre']} | Género: {cat['genero']}")

# Contar partidos por categoría
print("\n=== PARTIDOS POR CATEGORÍA ===\n")
for cat in categorias:
    cur.execute("""
        SELECT COUNT(*) as total
        FROM partidos
        WHERE id_torneo = 46 AND categoria_id = %s
    """, (cat['id'],))
    
    result = cur.fetchone()
    print(f"{cat['nombre']}: {result['total']} partidos")

cur.close()
conn.close()
