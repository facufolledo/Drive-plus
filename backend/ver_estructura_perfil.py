"""
Ver estructura de perfil_usuarios
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Ver columnas de perfil_usuarios
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'perfil_usuarios'
    ORDER BY ordinal_position
""")

print("Columnas de perfil_usuarios:")
for col, tipo in cur.fetchall():
    print(f"  - {col}: {tipo}")

# Ver si hay tabla de historial de categorías
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%categoria%'
    OR table_name LIKE '%historial%'
""")

print("\nTablas relacionadas con categorías/historial:")
for tabla in cur.fetchall():
    print(f"  - {tabla[0]}")

cur.close()
conn.close()
