#!/usr/bin/env python3
"""Ver horarios actuales del torneo 45"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import json

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, nombre, horarios_disponibles FROM torneos WHERE id = 45")).fetchone()
    print(f"Torneo: {result[1]}")
    print("\nHorarios disponibles:")
    if result[2]:
        print(json.dumps(result[2], indent=2, ensure_ascii=False))
    else:
        print("NULL")
