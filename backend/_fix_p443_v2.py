import os, sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

DURACION = timedelta(minutes=50)

with engine.connect() as c:
    # Ver todos los partidos del viernes en canchas 5,6,7 para encontrar hueco
    print("=== PARTIDOS VIE 20/02 POR CANCHA ===")
    for cid, cname in [(76,"Cancha 5"), (77,"Cancha 6"), (78,"Cancha 7")]:
        partidos = c.execute(text("""
            SELECT id_partido, fecha_hora FROM partidos
            WHERE id_torneo = 38 AND cancha_id = :c AND fecha_hora::date = '2026-02-20'
            ORDER BY fecha_hora
        """), {"c": cid}).fetchall()
        print(f"\n  {cname}:")
        for p in partidos:
            fh = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
            fin = fh + DURACION
            print(f"    P{p[0]} {fh.strftime('%H:%M')}-{fin.strftime('%H:%M')}")

    # También ver sábado temprano
    print("\n=== PARTIDOS SÁB 21/02 POR CANCHA (hasta 12:00) ===")
    for cid, cname in [(76,"Cancha 5"), (77,"Cancha 6"), (78,"Cancha 7")]:
        partidos = c.execute(text("""
            SELECT id_partido, fecha_hora FROM partidos
            WHERE id_torneo = 38 AND cancha_id = :c AND fecha_hora::date = '2026-02-21' AND EXTRACT(HOUR FROM fecha_hora) < 12
            ORDER BY fecha_hora
        """), {"c": cid}).fetchall()
        print(f"\n  {cname}:")
        for p in partidos:
            fh = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
            fin = fh + DURACION
            print(f"    P{p[0]} {fh.strftime('%H:%M')}-{fin.strftime('%H:%M')}")

    # Info de P443
    print("\n=== P443 INFO ===")
    r = c.execute(text("""
        SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.zona_id, p.categoria_id
        FROM partidos p WHERE p.id_partido = 443
    """)).fetchone()
    print(f"  P{r[0]}: parejas {r[1]} vs {r[2]}, zona={r[3]}, cat={r[4]}")

    # Ver otros partidos de estas parejas para no crear conflicto de descanso
    for pid in [r[1], r[2]]:
        pts = c.execute(text("""
            SELECT p.id_partido, p.fecha_hora, p.cancha_id
            FROM partidos p
            WHERE p.id_torneo = 38 AND (p.pareja1_id = :p OR p.pareja2_id = :p) AND p.id_partido != 443
            ORDER BY p.fecha_hora
        """), {"p": pid}).fetchall()
        print(f"  Pareja {pid} otros partidos:")
        for pt in pts:
            fh = pt[1].replace(tzinfo=None) if pt[1].tzinfo else pt[1]
            print(f"    P{pt[0]} {fh.strftime('%a %d/%m %H:%M')} cancha={pt[2]}")
