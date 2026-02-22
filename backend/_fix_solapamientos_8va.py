"""Resolver solapamientos de cancha de 8va"""
import os, sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

DURACION = timedelta(minutes=50)

with engine.connect() as c:
    # Verificar Cancha 7 a las 23:00 vie
    print("=== Cancha 7 vie 23:00 ===")
    pts = c.execute(text("""
        SELECT id_partido, fecha_hora FROM partidos
        WHERE id_torneo = 38 AND cancha_id = 78 AND fecha_hora::date = '2026-02-20'
        ORDER BY fecha_hora
    """)).fetchall()
    for p in pts:
        fh = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
        print(f"  P{p[0]} {fh.strftime('%H:%M')}-{(fh+DURACION).strftime('%H:%M')}")

    # Verificar Cancha 6 sáb 15:00
    print("\n=== Cancha 6 sáb 15:00 ===")
    pts = c.execute(text("""
        SELECT id_partido, fecha_hora FROM partidos
        WHERE id_torneo = 38 AND cancha_id = 77 AND fecha_hora::date = '2026-02-21'
        ORDER BY fecha_hora
    """)).fetchall()
    for p in pts:
        fh = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
        print(f"  P{p[0]} {fh.strftime('%H:%M')}-{(fh+DURACION).strftime('%H:%M')}")

    # Verificar Cancha 7 sáb 15:00
    print("\n=== Cancha 7 sáb 15:00 ===")
    pts = c.execute(text("""
        SELECT id_partido, fecha_hora FROM partidos
        WHERE id_torneo = 38 AND cancha_id = 78 AND fecha_hora::date = '2026-02-21'
        ORDER BY fecha_hora
    """)).fetchall()
    for p in pts:
        fh = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
        print(f"  P{p[0]} {fh.strftime('%H:%M')}-{(fh+DURACION).strftime('%H:%M')}")
