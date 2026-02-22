"""Actualizar restricción pareja 645 (Ferreyra/Gudiño): viernes no pueden 09-14 ni 16-22"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

restricciones = json.dumps([
    {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "14:00"},
    {"dias": ["viernes"], "horaInicio": "16:00", "horaFin": "22:00"}
])
s.execute(text("UPDATE torneos_parejas SET disponibilidad_horaria = CAST(:r AS jsonb) WHERE id = 645"), {"r": restricciones})
s.commit()
row = s.execute(text("SELECT disponibilidad_horaria FROM torneos_parejas WHERE id = 645")).fetchone()
print("Pareja 645 restricciones:", row[0])
s.close()
