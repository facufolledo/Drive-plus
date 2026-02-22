import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as c:
    restricciones = [
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
        {"dias": ["viernes"], "horaInicio": "17:00", "horaFin": "22:00"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "15:00"},
        {"dias": ["sabado"], "horaInicio": "17:00", "horaFin": "22:00"},
    ]
    c.execute(text("UPDATE torneos_parejas SET disponibilidad_horaria = CAST(:r AS jsonb) WHERE id = 655"),
              {"r": json.dumps(restricciones)})
    c.commit()
    r = c.execute(text("SELECT disponibilidad_horaria FROM torneos_parejas WHERE id = 655")).fetchone()
    print("OK:", json.dumps(r[0], ensure_ascii=False, indent=2))
