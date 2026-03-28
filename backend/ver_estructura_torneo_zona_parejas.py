import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'torneo_zona_parejas' 
    ORDER BY ordinal_position
""")

print("Columnas de torneo_zona_parejas:")
for col in cur.fetchall():
    print(f"  {col[0]}: {col[1]}")

cur.close()
conn.close()
