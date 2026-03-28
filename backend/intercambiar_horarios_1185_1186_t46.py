import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor()

try:
    print("🔨 Intercambiando horarios de partidos 1185 y 1186...")
    print("  Partido 1186: 17:30 → 14:00")
    print("  Partido 1185: 14:00 → 17:30")
    
    # Partido 1186 a las 14:00
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 14:00:00'
        WHERE id_partido = 1186
    """)
    
    # Partido 1185 a las 17:30
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 17:30:00'
        WHERE id_partido = 1185
    """)
    
    conn.commit()
    print("✅ Horarios intercambiados correctamente")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
finally:
    cur.close()
    conn.close()
