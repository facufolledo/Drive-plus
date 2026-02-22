import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as c:
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, p.pareja1_id, p.pareja2_id, p.categoria_id, p.estado
        FROM partidos p
        WHERE p.id_torneo = 38 AND p.fecha_hora IS NOT NULL AND p.fecha_hora < '2026-01-01'
    """)).fetchall()
    for r in rows:
        print(f"P{r[0]} | fecha: {r[1]} | cancha: {r[2]} | p1: {r[3]} p2: {r[4]} | cat: {r[5]} | estado: {r[6]}")
