"""Buscar jugadores para inscribir en torneo 38"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

print("=== Buscar jugadores ===")
buscar = ['ruarte', 'ellerak', 'oliva', 'cruz']
for b in buscar:
    rows = s.execute(text(
        "SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido "
        "FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario "
        "WHERE LOWER(u.nombre_usuario) LIKE :q OR LOWER(p.apellido) LIKE :q OR LOWER(p.nombre) LIKE :q"
    ), {"q": f"%{b}%"}).fetchall()
    print(f"\n'{b}':")
    if rows:
        for r in rows:
            print(f"  ID={r[0]}, user={r[1]}, email={r[2]}, perfil={r[3]} {r[4]}")
    else:
        print("  No encontrado")

print("\n=== Columnas categorias ===")
cols = s.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'categorias' ORDER BY ordinal_position")).fetchall()
print([c[0] for c in cols])

print("\n=== Categoría 6ta torneo 38 ===")
cats = s.execute(text("SELECT id_categoria, nombre FROM categorias WHERE torneo_id = 38")).fetchall()
for c in cats:
    print(f"  Cat ID={c[0]}, nombre={c[1]}")

print("\n=== Parejas actuales en 6ta ===")
cat_6ta = [c[0] for c in cats if '6' in str(c[1]).lower()]
if cat_6ta:
    parejas = s.execute(text(
        "SELECT tp.id, tp.jugador1_id, tp.jugador2_id, p1.nombre, p1.apellido, p2.nombre, p2.apellido "
        "FROM torneos_parejas tp "
        "LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario "
        "LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario "
        "WHERE tp.torneo_id = 38 AND tp.categoria_id = :c"
    ), {"c": cat_6ta[0]}).fetchall()
    print(f"  Total: {len(parejas)}")
    for p in parejas:
        print(f"  Pareja {p[0]}: {p[3]} {p[4]} (ID {p[1]}) + {p[5]} {p[6]} (ID {p[2]})")

s.close()
