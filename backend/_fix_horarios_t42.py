"""Corregir horarios del Torneo 42 - solo viernes, sábado y domingo"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 42

# Horarios correctos: solo viernes, sábado y domingo
horarios_correctos = {
    "viernes": {"inicio": "15:00", "fin": "23:30"},
    "sabado": {"inicio": "09:00", "fin": "23:30"},
    "domingo": {"inicio": "09:00", "fin": "23:30"}
}

with engine.connect() as conn:
    print("=== CORRIGIENDO HORARIOS TORNEO 42 ===\n")
    
    # Verificar horarios actuales
    torneo = conn.execute(text("""
        SELECT horarios_disponibles FROM torneos WHERE id = :tid
    """), {"tid": TORNEO_ID}).fetchone()
    
    print("Horarios actuales:")
    print(json.dumps(torneo[0], indent=2))
    
    # Actualizar horarios
    conn.execute(text("""
        UPDATE torneos 
        SET horarios_disponibles = CAST(:horarios AS jsonb)
        WHERE id = :tid
    """), {"horarios": json.dumps(horarios_correctos), "tid": TORNEO_ID})
    
    # Verificar después
    torneo_nuevo = conn.execute(text("""
        SELECT horarios_disponibles FROM torneos WHERE id = :tid
    """), {"tid": TORNEO_ID}).fetchone()
    
    print("\nHorarios nuevos:")
    print(json.dumps(torneo_nuevo[0], indent=2))
    
    conn.commit()
    print("\n✅ Horarios actualizados correctamente!")
