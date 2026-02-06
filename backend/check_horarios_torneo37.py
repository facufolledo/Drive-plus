"""
Script para verificar formato de horarios del torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def check_horarios():
    session = Session()
    
    try:
        result = session.execute(
            text("SELECT horarios_disponibles FROM torneos WHERE id = 37")
        ).fetchone()
        
        if result and result[0]:
            print("Formato de horarios:")
            print(json.dumps(result[0], indent=2))
        else:
            print("No hay horarios configurados")
            
    finally:
        session.close()

if __name__ == "__main__":
    check_horarios()
