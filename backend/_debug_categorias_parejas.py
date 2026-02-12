"""Debug: ver qué categorías tienen las parejas del torneo 37"""
import pg8000, os
from dotenv import load_dotenv
load_dotenv()

db_url = os.getenv("DATABASE_URL", "")
parts = db_url.replace("postgresql+pg8000://", "").split("@")
user_pass = parts[0].split(":")
host_db = parts[1].split("/")

conn = pg8000.connect(user=user_pass[0], password=user_pass[1], host=host_db[0], database=host_db[1], ssl_context=True)
cur = conn.cursor()

# Ver categorias de parejas torneo 37
print("Parejas torneo 37 con categoría:")
cur.execute("""
    SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.categoria_asignada, tp.categoria_id,
           tc.nombre as cat_nombre
    FROM torneos_parejas tp
    LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
    WHERE tp.torneo_id = 37
    LIMIT 20
""")
for r in cur.fetchall():
    print(f"  pareja={r[0]}, j1={r[1]}, j2={r[2]}, cat_asignada='{r[3]}', cat_id={r[4]}, cat_nombre='{r[5]}'")

# Ver torneo_categorias del torneo 37
print("\nCategorías del torneo 37:")
cur.execute("SELECT id, nombre, genero FROM torneo_categorias WHERE torneo_id = 37")
for r in cur.fetchall():
    print(f"  id={r[0]}, nombre='{r[1]}', genero='{r[2]}'")

# Ver partidos y cómo se relacionan con parejas
print("\nPartidos torneo 37 con parejas (primeros 5):")
cur.execute("""
    SELECT p.id_partido, p.id_torneo, p.equipo1_id, p.equipo2_id, p.estado
    FROM partidos p
    WHERE p.id_torneo = 37 AND p.estado IN ('finalizado', 'confirmado')
    LIMIT 5
""")
partidos = cur.fetchall()
for r in partidos:
    print(f"  partido={r[0]}, equipo1={r[2]}, equipo2={r[3]}, estado='{r[4]}'")

# Ver columnas de partidos
print("\nColumnas de partidos:")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'partidos' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r[0]}")

conn.close()
