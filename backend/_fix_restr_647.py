import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()
row = s.execute(text("SELECT disponibilidad_horaria FROM torneos_parejas WHERE id = 647")).fetchone()
print(f"Restricciones actuales pareja 647: {row[0]}")
if not row[0]:
    r = json.dumps([
        {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "20:00"},
        {"dias": ["domingo"], "horaInicio": "09:00", "horaFin": "15:00"}
    ])
    s.execute(text("UPDATE torneos_parejas SET disponibilidad_horaria = CAST(:r AS jsonb) WHERE id = 647"), {"r": r})
    s.commit()
    print("✅ Restricciones actualizadas")
else:
    print("Ya tiene restricciones")
s.close()
