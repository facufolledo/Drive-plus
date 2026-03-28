#!/usr/bin/env python3
"""
Ver canchas del torneo 45
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def main():
    s = Session()
    try:
        canchas = s.execute(text("""
            SELECT id, nombre, activa FROM torneo_canchas
            WHERE torneo_id = :t
            ORDER BY nombre
        """), {"t": TORNEO_ID}).fetchall()
        
        print(f"Canchas del torneo {TORNEO_ID}:")
        for c in canchas:
            print(f"  ID: {c.id}, Nombre: {c.nombre}, Activa: {c.activa}")
    finally:
        s.close()

if __name__ == "__main__":
    main()
