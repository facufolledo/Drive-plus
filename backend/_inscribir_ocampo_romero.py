"""Inscribir Ocampo + Romero en 4ta torneo 38"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

# Buscar
for q in ['ocampo', 'romero']:
    rows = s.execute(text(
        "SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido "
        "FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario "
        "WHERE LOWER(p.apellido) LIKE :q OR LOWER(u.nombre_usuario) LIKE :q"
    ), {"q": f"%{q}%"}).fetchall()
    print(f"'{q}':")
    if rows:
        for r in rows:
            print(f"  ID={r[0]}, user={r[1]}, email={r[2]}, perfil={r[3]} {r[4]}")
    else:
        print("  No encontrado")

s.close()
