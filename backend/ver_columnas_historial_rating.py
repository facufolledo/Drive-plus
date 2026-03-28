import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor()

cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'historial_rating' 
    ORDER BY ordinal_position
""")

print("Columnas de historial_rating:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

cur.close()
conn.close()
