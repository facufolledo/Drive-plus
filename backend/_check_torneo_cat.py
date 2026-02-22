"""Verificar categorías del torneo 38"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

# Columnas de torneo_categorias
print("=== Columnas torneo_categorias ===")
cols = s.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'torneo_categorias' ORDER BY ordinal_position")).fetchall()
print([c[0] for c in cols])

# Categorías del torneo 38
print("\n=== torneo_categorias para torneo 38 ===")
tc = s.execute(text("SELECT * FROM torneo_categorias WHERE torneo_id = 38")).fetchall()
for r in tc:
    print(f"  {r}")

# Si no hay, ver torneo 37 como referencia
print("\n=== torneo_categorias para torneo 37 ===")
tc37 = s.execute(text("SELECT * FROM torneo_categorias WHERE torneo_id = 37")).fetchall()
for r in tc37:
    print(f"  {r}")

# Parejas del torneo 38 y sus categorías
print("\n=== Categorías usadas en parejas torneo 38 ===")
used = s.execute(text("SELECT DISTINCT categoria_id FROM torneos_parejas WHERE torneo_id = 38")).fetchall()
print(f"  {[u[0] for u in used]}")

s.close()
