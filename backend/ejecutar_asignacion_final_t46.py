import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

def conectar_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url.startswith('postgresql+pg8000://'):
        db_url = db_url.replace('postgresql+pg8000://', 'postgresql://')
    return psycopg2.connect(db_url)

asignaciones = [
    (1044, datetime(2026, 3, 29, 16, 0), 'Sabado 16:00'),
    (1045, datetime(2026, 3, 29, 17, 0), 'Sabado 17:00'),
    (1046, datetime(2026, 3, 28, 23, 59), 'Viernes 23:59'),
    (1052, datetime(2026, 3, 28, 22, 30), 'Viernes 22:30')
]

print("\nAsignando horarios finales...")
print("-" * 50)

conn = conectar_db()
cur = conn.cursor()

for partido_id, fecha, desc in asignaciones:
    cur.execute("""
        UPDATE partidos 
        SET fecha_hora = %s
        WHERE id_partido = %s
    """, (fecha, partido_id))
    print(f"Partido {partido_id}: {desc}")

conn.commit()
cur.close()
conn.close()

print("\nOK - 4 partidos actualizados")
