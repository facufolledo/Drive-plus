"""Buscar Cruz Juan en la app"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

# Buscar "cruz" en apellido (no nombre, porque Juan Cruz Folledo no es)
rows = s.execute(text(
    "SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido "
    "FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario "
    "WHERE LOWER(p.apellido) LIKE :q"
), {"q": "%cruz%"}).fetchall()
print("Apellido 'cruz':")
for r in rows:
    print(f"  ID={r[0]}, user={r[1]}, email={r[2]}, perfil={r[3]} {r[4]}")
if not rows:
    print("  No encontrado")

# Buscar también por nombre_usuario
rows2 = s.execute(text(
    "SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido "
    "FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario "
    "WHERE LOWER(u.nombre_usuario) LIKE :q AND u.id_usuario != 10"
), {"q": "%cruz%"}).fetchall()
print("\nUsername 'cruz' (excl ID 10):")
for r in rows2:
    print(f"  ID={r[0]}, user={r[1]}, email={r[2]}, perfil={r[3]} {r[4]}")
if not rows2:
    print("  No encontrado")

# Oliva ya es temp (ID 200), verificar si tiene perfil
print("\n=== Oliva Bautista (ID 200) ===")
r = s.execute(text("SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario WHERE u.id_usuario = 200")).fetchone()
if r:
    print(f"  ID={r[0]}, user={r[1]}, email={r[2]}, perfil={r[3]} {r[4]}")

# Parejas actuales en cat 88
print("\n=== Parejas en cat 88 (6ta) torneo 38 ===")
parejas = s.execute(text(
    "SELECT tp.id, tp.jugador1_id, tp.jugador2_id, p1.nombre, p1.apellido, p2.nombre, p2.apellido "
    "FROM torneos_parejas tp "
    "LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario "
    "LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario "
    "WHERE tp.torneo_id = 38 AND tp.categoria_id = 88"
)).fetchall()
print(f"  Total: {len(parejas)}")
for p in parejas:
    print(f"  Pareja {p[0]}: {p[3]} {p[4]} (ID {p[1]}) + {p[5]} {p[6]} (ID {p[2]})")

s.close()
