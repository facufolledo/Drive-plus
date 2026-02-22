"""Cambiar pareja de Magi: sacar Mercado, poner Arrebola Jeremías"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

# Buscar Arrebola
rows = s.execute(text(
    "SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido "
    "FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario "
    "WHERE LOWER(p.apellido) LIKE :q OR LOWER(u.nombre_usuario) LIKE :q"
), {"q": "%arrebola%"}).fetchall()
print("Arrebola:")
for r in rows:
    print(f"  ID={r[0]}, user={r[1]}, email={r[2]}, perfil={r[3]} {r[4]}")

# Buscar pareja de Magi en 4ta torneo 38
print("\nPareja de Magi (ID 511) en torneo 38:")
p = s.execute(text(
    "SELECT tp.id, tp.jugador1_id, tp.jugador2_id, p1.nombre, p1.apellido, p2.nombre, p2.apellido "
    "FROM torneos_parejas tp "
    "LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario "
    "LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario "
    "WHERE tp.torneo_id = 38 AND tp.categoria_id = 87 AND (tp.jugador1_id = 511 OR tp.jugador2_id = 511)"
)).fetchall()
for r in p:
    print(f"  Pareja ID={r[0]}: {r[3]} {r[4]} (ID {r[1]}) + {r[5]} {r[6]} (ID {r[2]})")

s.close()
