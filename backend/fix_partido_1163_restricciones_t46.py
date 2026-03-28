import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor()

try:
    print("🔨 Corrigiendo partido 1163...")
    print("\n  Restricciones:")
    print("    - Facundo Martín / Pablo Samir: NO viernes 19:00-23:59")
    print("    - Luciano Paez / Juan Córdoba: NO viernes 20:00-23:59")
    print("\n  Horario actual: Viernes 20:00 (VIOLA ambas restricciones)")
    print("  Nuevo horario: Viernes 17:00 (respeta ambas restricciones)")
    
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 17:00:00'
        WHERE id_partido = 1163
    """)
    
    conn.commit()
    print("\n✅ Partido 1163 movido a viernes 17:00")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
finally:
    cur.close()
    conn.close()
