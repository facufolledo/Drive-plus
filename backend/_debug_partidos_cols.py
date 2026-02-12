import pg8000, os
from dotenv import load_dotenv
load_dotenv()
db_url = os.getenv("DATABASE_URL", "")
parts = db_url.replace("postgresql+pg8000://", "").split("@")
up = parts[0].split(":")
hd = parts[1].split("/")
conn = pg8000.connect(user=up[0], password=up[1], host=hd[0], database=hd[1], ssl_context=True)
cur = conn.cursor()

print("Columnas de partidos:")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'partidos' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r[0]}")

print("\nEjemplo partido torneo 37:")
cur.execute("SELECT * FROM partidos WHERE id_torneo = 37 AND estado = 'confirmado' LIMIT 1")
cols = [d[0] for d in cur.description]
row = cur.fetchone()
if row:
    for c, v in zip(cols, row):
        print(f"  {c} = {v}")

# Relacion partido -> pareja -> categoria
print("\nPartido -> pareja -> categoria (5 ejemplos):")
cur.execute("""
    SELECT p.id_partido, p.pareja1_id, p.pareja2_id,
           tp1.categoria_id as cat1_id, tc1.nombre as cat1_nombre,
           tp2.categoria_id as cat2_id, tc2.nombre as cat2_nombre
    FROM partidos p
    LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    LEFT JOIN torneo_categorias tc1 ON tp1.categoria_id = tc1.id
    LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    LEFT JOIN torneo_categorias tc2 ON tp2.categoria_id = tc2.id
    WHERE p.id_torneo = 37 AND p.estado = 'confirmado'
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"  partido={r[0]}, p1={r[1]}(cat:{r[4]}), p2={r[2]}(cat:{r[6]})")

conn.close()
