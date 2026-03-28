import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'usuarios'
    ORDER BY ordinal_position
""")

columns = cur.fetchall()

print("Estructura de usuarios:")
for col in columns:
    print(f"  {col['column_name']}: {col['data_type']} - Nullable: {col['is_nullable']} - Default: {col['column_default']}")

cur.close()
conn.close()
