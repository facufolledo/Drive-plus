import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor()

try:
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 23:59:00'
        WHERE id_partido = 1185
    """)
    
    conn.commit()
    print("✅ Partido 1185 movido a viernes 27 marzo 23:59")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
finally:
    cur.close()
    conn.close()
