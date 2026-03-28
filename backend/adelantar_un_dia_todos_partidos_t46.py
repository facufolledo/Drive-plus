import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

def conectar_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url.startswith('postgresql+pg8000://'):
        db_url = db_url.replace('postgresql+pg8000://', 'postgresql://')
    return psycopg2.connect(db_url)

print("\nAdelantando todos los partidos de 7ma un dia...")
print("-" * 50)

conn = conectar_db()
cur = conn.cursor()

# Adelantar todos los partidos de 7ma del torneo 46 un dia
cur.execute("""
    UPDATE partidos 
    SET fecha_hora = fecha_hora + INTERVAL '1 day'
    WHERE id_torneo = 46
    AND categoria_id = 126
    AND fase = 'zona'
""")

affected = cur.rowcount
conn.commit()

print(f"OK - {affected} partidos adelantados un dia")
print("\nAhora:")
print("  28 marzo (sabado) -> 29 marzo (domingo)")
print("  29 marzo (domingo) -> 30 marzo (lunes)")
print("\nVerificando...")

cur.execute("""
    SELECT 
        DATE(fecha_hora) as fecha,
        COUNT(*) as total
    FROM partidos
    WHERE id_torneo = 46
    AND categoria_id = 126
    AND fase = 'zona'
    GROUP BY DATE(fecha_hora)
    ORDER BY fecha
""")

for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} partidos")

cur.close()
conn.close()
