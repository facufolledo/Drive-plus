import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

# Ver estructura de la tabla
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'perfil_usuarios'
    ORDER BY ordinal_position
""")

print("Columnas de perfil_usuarios:")
for col in cur.fetchall():
    print(f"  - {col['column_name']}: {col['data_type']}")

cur.close()
conn.close()
