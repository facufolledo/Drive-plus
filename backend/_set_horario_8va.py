"""Poner horario 2026-02-22 11:00 al partido de 8va entre PA647 y PA652"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Buscar el partido
    r = conn.execute(text("""
        SELECT id_partido, pareja1_id, pareja2_id, fase, estado, fecha_hora
        FROM partidos
        WHERE id_torneo = 38
          AND fase != 'zona'
          AND (pareja1_id = 647 OR pareja2_id = 647)
          AND (pareja1_id = 652 OR pareja2_id = 652)
    """)).fetchall()
    
    for row in r:
        print(f"P{row[0]}: PA{row[1]} vs PA{row[2]} | fase={row[3]} estado={row[4]} fecha_hora={row[5]}")
    
    if r:
        pid = r[0][0]
        conn.execute(text("UPDATE partidos SET fecha_hora = '2026-02-22 11:00:00' WHERE id_partido = :pid"), {"pid": pid})
        conn.commit()
        print(f"\n✅ Horario actualizado: P{pid} -> 2026-02-22 11:00")
    else:
        print("❌ No se encontró el partido")
