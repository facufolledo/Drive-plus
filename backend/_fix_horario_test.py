"""Fix horario de prueba P587 - poner 11:00 como naive (sin timezone)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text
from datetime import datetime

db = SessionLocal()
# Poner 11:00 como hora local (naive, sin timezone)
db.execute(text("UPDATE partidos SET fecha_hora = '2026-02-22 11:00:00' WHERE id_partido = 587"))
db.commit()
print("P587 actualizado a 2026-02-22 11:00:00 (naive)")
db.close()
