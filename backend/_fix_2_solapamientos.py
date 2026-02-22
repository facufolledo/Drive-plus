import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # P439: Quiroz vs Calderón 21:00 C5 -> C7
    c.execute(text("UPDATE partidos SET cancha_id = 78 WHERE id_partido = 439"))
    print("P439: Cancha 5 -> Cancha 7 (21:00) ✅")

    # P396: Moreno/Nieto vs Ligorria/Brizuela 22:30 C6 -> 22:50 C6
    c.execute(text("UPDATE partidos SET fecha_hora = '2026-02-20 22:50:00' WHERE id_partido = 396"))
    print("P396: 22:30 -> 22:50 Cancha 6 ✅")

    c.commit()
