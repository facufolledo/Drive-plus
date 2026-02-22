import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as c:
    r = c.execute(text("SELECT disponibilidad_horaria FROM torneos_parejas WHERE id = 655")).fetchone()
    actual = r[0] if isinstance(r[0], list) else (json.loads(r[0]) if r[0] else [])
    print("ANTES:", json.dumps(actual, ensure_ascii=False))
    
    # Agregar misma restriccion para sabado: 09-15 y 17-22
    actual.append({"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "15:00"})
    actual.append({"dias": ["sabado"], "horaInicio": "17:00", "horaFin": "22:00"})
    
    c.execute(text("UPDATE torneos_parejas SET disponibilidad_horaria = CAST(:r AS jsonb) WHERE id = 655"),
              {"r": json.dumps(actual)})
    c.commit()
    
    r2 = c.execute(text("SELECT disponibilidad_horaria FROM torneos_parejas WHERE id = 655")).fetchone()
    datos = r2[0] if isinstance(r2[0], list) else json.loads(r2[0])
    print("DESPUES:", json.dumps(datos, ensure_ascii=False, indent=2))
