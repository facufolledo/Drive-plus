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

print("\nRestando 2 dias a todos los partidos de 7ma...")
print("-" * 50)

conn = conectar_db()
cur = conn.cursor()

# Restar 2 dias (para compensar el +1 anterior y quedar en -1 total)
cur.execute("""
    UPDATE partidos 
    SET fecha_hora = fecha_hora - INTERVAL '2 days'
    WHERE id_torneo = 46
    AND categoria_id = 126
    AND fase = 'zona'
""")

affected = cur.rowcount
conn.commit()

print(f"OK - {affected} partidos actualizados")
print("\nVerificando fechas finales...")

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

print("\nListo! Ahora deberian estar en viernes 27 y sabado 28")
