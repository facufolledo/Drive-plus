import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor()

print("=" * 80)
print("AJUSTE PARTIDO 1168 - HORARIO MÁS RAZONABLE")
print("=" * 80)

# Mover a sábado 15:00 (horario más razonable después de 14:30)
nuevo_horario = '2026-03-28 15:00:00'

cur.execute("""
    UPDATE partidos
    SET fecha_hora = %s
    WHERE id_partido = 1168
""", (nuevo_horario,))

conn.commit()

print(f"\n✅ Partido 1168 ajustado a sábado 15:00")
print(f"   (Horario más razonable que 23:30)")

cur.close()
conn.close()
