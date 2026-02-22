import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as c:
    c.execute(text("UPDATE partidos SET fecha_hora = '2026-02-20 22:00:00' WHERE id_partido = 392"))
    c.commit()
    r = c.execute(text("SELECT id_partido, fecha_hora FROM partidos WHERE id_partido = 392")).fetchone()
    print(f"P{r[0]} -> {r[1]}")
