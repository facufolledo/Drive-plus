"""Buscar categoría 4ta y Calderón"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

# Todas las categorías
print("=== Todas las categorías ===")
cats = s.execute(text("SELECT id_categoria, nombre FROM categorias")).fetchall()
for c in cats:
    print(f"  ID={c[0]}, nombre={c[1]}")

# Buscar Calderón con variantes
print("\n=== Buscar Calderón ===")
for q in ['calder', 'calderon']:
    rows = s.execute(text(
        "SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido "
        "FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario "
        "WHERE LOWER(p.apellido) LIKE :q OR LOWER(u.nombre_usuario) LIKE :q"
    ), {"q": f"%{q}%"}).fetchall()
    print(f"  '{q}':")
    for r in rows:
        print(f"    ID={r[0]}, user={r[1]}, email={r[2]}, perfil={r[3]} {r[4]}")

# Buscar categorías del torneo 38 directamente
print("\n=== Categorías vinculadas a torneo 38 ===")
# Puede ser via torneos_categorias o similar
tables = s.execute(text(
    "SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%categ%' OR table_name LIKE '%torneo%categ%'"
)).fetchall()
print(f"  Tablas: {[t[0] for t in tables]}")

# Probar torneos_categorias
try:
    tc = s.execute(text("SELECT * FROM torneos_categorias WHERE torneo_id = 38")).fetchall()
    print(f"  torneos_categorias: {tc}")
except:
    print("  No existe torneos_categorias")

# La categoría 88 es 6ta. Buscar 4ta
for c in cats:
    if '4' in str(c[1]):
        print(f"\n  Posible 4ta: ID={c[0]}, nombre={c[1]}")

s.close()
