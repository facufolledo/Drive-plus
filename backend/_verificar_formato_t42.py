"""Verificar formato de horarios del Torneo 42"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("=== VERIFICAR FORMATO HORARIOS T42 ===\n")
    
    torneo = conn.execute(text("""
        SELECT id, nombre, horarios_disponibles
        FROM torneos WHERE id = 42
    """)).fetchone()
    
    print(f"Torneo {torneo[0]}: {torneo[1]}")
    print(f"\nFormato actual:")
    horarios = torneo[2]
    print(json.dumps(horarios, indent=2))
    
    # Verificar si es formato correcto (por día)
    if isinstance(horarios, dict):
        dias_validos = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        es_formato_dia = all(k in dias_validos for k in horarios.keys())
        
        if es_formato_dia:
            print("\n✅ Formato correcto: por día {dia: {inicio, fin}}")
        else:
            print("\n⚠️ Formato desconocido")
    elif isinstance(horarios, list):
        print("\n❌ Formato incorrecto: array [{dias: [], horaInicio, horaFin}]")
        print("   Necesita convertirse a formato por día")
    else:
        print("\n❌ Formato inválido")
