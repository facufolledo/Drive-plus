import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as c:
    # Mover P391 de Cancha 5 (76) a Cancha 7 (78)
    c.execute(text("UPDATE partidos SET cancha_id = 78 WHERE id_partido = 391"))
    c.commit()
    r = c.execute(text("SELECT id_partido, cancha_id FROM partidos WHERE id_partido = 391")).fetchone()
    print(f"P{r[0]} -> cancha_id: {r[1]} (Cancha 7)")
