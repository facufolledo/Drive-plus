import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as c:
    c.execute(text("UPDATE partidos SET cancha_id = 78 WHERE id_partido = 399"))
    c.commit()
    r = c.execute(text("SELECT id_partido, fecha_hora, cancha_id FROM partidos WHERE id_partido = 399")).fetchone()
    print(f"P{r[0]} -> {r[1]} cancha_id={r[2]} (Cancha 7)")
