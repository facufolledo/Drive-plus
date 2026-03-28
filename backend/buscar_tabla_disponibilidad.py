import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor()

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%disponibilidad%'
""")

print("Tablas con 'disponibilidad':")
for row in cur.fetchall():
    print(f"  - {row[0]}")

cur.close()
conn.close()
