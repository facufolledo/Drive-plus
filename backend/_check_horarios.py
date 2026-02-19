import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=e)()

# Comparar horarios del torneo 37 vs 41
for tid in [37, 41]:
    r = s.execute(text("SELECT id, nombre, horarios_disponibles FROM torneos WHERE id = :t"), {"t": tid}).fetchone()
    if r:
        print(f"\nTorneo {r[0]}: {r[1]}")
        print(f"  horarios_disponibles = {r[2]}")
        print(f"  tipo = {type(r[2])}")
s.close()
