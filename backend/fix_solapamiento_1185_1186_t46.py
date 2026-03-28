import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor()

try:
    # Mover partido 1186 de 15:00 a 17:30 para dar más separación
    print("🔨 Ajustando partido 1186...")
    print("  Actual: Sábado 15:00")
    print("  Nueva: Sábado 17:30")
    
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 17:30:00'
        WHERE id_partido = 1186
    """)
    
    conn.commit()
    print("✅ Partido 1186 movido a sábado 17:30")
    print("   Separación con partido 1185: 210 minutos (3.5 horas)")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
finally:
    cur.close()
    conn.close()
