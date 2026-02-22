"""Setear horario de prueba en un partido de playoff"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text
from datetime import datetime

db = SessionLocal()

# Buscar el partido de 4ta con parejas 643 vs 636
r = db.execute(text("""
    SELECT id_partido, fase, pareja1_id, pareja2_id, estado, fecha_hora
    FROM partidos 
    WHERE id_torneo = 38 AND categoria_id = 87
      AND ((pareja1_id = 643 AND pareja2_id = 636) OR (pareja1_id = 636 AND pareja2_id = 643))
""")).fetchall()

for p in r:
    print(f"P{p[0]}: {p[1]} p1={p[2]} p2={p[3]} estado={p[4]} fecha_hora={p[5]}")

if r:
    pid = r[0][0]
    # Hoy 22 feb 2026 a las 11:00 AM Argentina (UTC-3)
    fecha = datetime(2026, 2, 22, 11, 0, 0)
    db.execute(text("UPDATE partidos SET fecha_hora = :fh WHERE id_partido = :pid"), 
               {"fh": fecha, "pid": pid})
    db.commit()
    print(f"\nActualizado P{pid} con fecha_hora = {fecha}")
else:
    print("No encontrado")

db.close()
