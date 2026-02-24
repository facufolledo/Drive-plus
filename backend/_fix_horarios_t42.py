"""Corregir horarios_disponibles del torneo 42 al formato por día"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# Formato correcto por día
horarios_nuevos = {
    "lunes": {"inicio": "15:00", "fin": "23:30"},
    "martes": {"inicio": "15:00", "fin": "23:30"},
    "miercoles": {"inicio": "15:00", "fin": "23:30"},
    "jueves": {"inicio": "15:00", "fin": "23:30"},
    "viernes": {"inicio": "09:00", "fin": "23:30"},
    "sabado": {"inicio": "09:00", "fin": "23:30"},
    "domingo": {"inicio": "09:00", "fin": "23:30"}
}

with engine.connect() as conn:
    conn.execute(
        text("UPDATE torneos SET horarios_disponibles = CAST(:h AS jsonb) WHERE id = 42"),
        {"h": json.dumps(horarios_nuevos)}
    )
    conn.commit()
    
    # Verificar
    result = conn.execute(text("SELECT horarios_disponibles FROM torneos WHERE id = 42")).fetchone()
    print(f"Horarios actualizados: {result[0]}")
    print("✅ Torneo 42 corregido")
