"""Mover P442 y P441 para resolver solapamientos con 4ta en Cancha 5"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # P442: Ocaña vs Palacio vie 23:00 -> Cancha 7 (libre a 23:00)
    c.execute(text("UPDATE partidos SET cancha_id = 78 WHERE id_partido = 442"))
    print("P442: Cancha 5 -> Cancha 7 (vie 23:00) ✅")

    # P441: Palma vs Palacio sáb 15:00 -> Cancha 6 (libre a 15:00)
    c.execute(text("UPDATE partidos SET cancha_id = 77 WHERE id_partido = 441"))
    print("P441: Cancha 5 -> Cancha 6 (sáb 15:00) ✅")

    c.commit()
    print("\nSolapamientos de 8va resueltos.")
