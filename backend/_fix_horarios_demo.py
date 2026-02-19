import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=e)()

horarios = {
    "viernes": {"inicio": "09:00", "fin": "23:00"},
    "sabado": {"inicio": "09:00", "fin": "23:00"}
}

s.execute(text("""
    UPDATE torneos SET horarios_disponibles = CAST(:h AS jsonb) WHERE id = 41
"""), {"h": json.dumps(horarios)})
s.commit()
print("✅ Horarios actualizados")

r = s.execute(text("SELECT horarios_disponibles FROM torneos WHERE id = 41")).fetchone()
print(f"Nuevo valor: {r[0]}")
s.close()
