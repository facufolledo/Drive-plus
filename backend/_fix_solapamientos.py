import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # P396: Cancha 6 vie 22:00 -> Cancha 6 vie 22:30
    c.execute(text("UPDATE partidos SET fecha_hora = '2026-02-20 22:30:00' WHERE id_partido = 396"))
    
    # P433: Cancha 5 sáb 14:50 -> Cancha 7 sáb 14:30
    c.execute(text("UPDATE partidos SET fecha_hora = '2026-02-21 14:30:00', cancha_id = 78 WHERE id_partido = 433"))
    
    c.commit()

    # Verificar
    for pid in [396, 433]:
        r = c.execute(text("SELECT id_partido, fecha_hora, cancha_id FROM partidos WHERE id_partido = :p"), {"p": pid}).fetchone()
        print(f"P{r[0]} -> {r[1]} cancha_id={r[2]}")
