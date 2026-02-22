"""Buscar jugadores para 4ta torneo 38 y verificar categoría"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

# Buscar categorías del torneo 38 via torneos_parejas
print("=== Categorías usadas en torneo 38 ===")
cats = s.execute(text(
    "SELECT DISTINCT tp.categoria_id, c.nombre FROM torneos_parejas tp "
    "JOIN categorias c ON tp.categoria_id = c.id_categoria "
    "WHERE tp.torneo_id = 38"
)).fetchall()
for c in cats:
    print(f"  Cat ID={c[0]}, nombre={c[1]}")

# Buscar jugadores que están en la app
buscar = ['nieto axel', 'calderon juan', 'nieto camilo', 'ligorria lisandro',
          'quipildor', 'brizuela amado', 'olivera matias', 'gurgone', 'magi juan',
          'mercado joaquin', 'rivero joaquin', 'centeno alejo', 'loto juan',
          'reyes emanuel', 'vallejos ariel', 'toledo emanuel', 'moreno aiken',
          'brizuela agustin']

print("\n=== Buscar jugadores ===")
for b in buscar:
    parts = b.split()
    if len(parts) == 2:
        rows = s.execute(text(
            "SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido "
            "FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario "
            "WHERE (LOWER(p.nombre) LIKE :n1 AND LOWER(p.apellido) LIKE :n2) "
            "OR (LOWER(p.apellido) LIKE :n1 AND LOWER(p.nombre) LIKE :n2) "
            "OR LOWER(u.nombre_usuario) LIKE :full"
        ), {"n1": f"%{parts[0]}%", "n2": f"%{parts[1]}%", "full": f"%{b.replace(' ','')}%"}).fetchall()
    else:
        rows = s.execute(text(
            "SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido "
            "FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario "
            "WHERE LOWER(p.apellido) LIKE :q OR LOWER(p.nombre) LIKE :q OR LOWER(u.nombre_usuario) LIKE :q"
        ), {"q": f"%{b}%"}).fetchall()
    print(f"\n  '{b}':")
    if rows:
        for r in rows:
            print(f"    ID={r[0]}, user={r[1]}, email={r[2]}, perfil={r[3]} {r[4]}")
    else:
        print(f"    No encontrado")

s.close()
