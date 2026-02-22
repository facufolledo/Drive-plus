import os, sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

DURACION = timedelta(minutes=50)
hora = datetime(2026, 2, 20, 22, 0)
fin = hora + DURACION

with engine.connect() as c:
    # Ver qué canchas están libres a las 22:00 del viernes (excepto cancha 8)
    print("=== CANCHAS A LAS 22:00 VIE 20/02 ===")
    for cid, cname in [(76,"Cancha 5"), (77,"Cancha 6"), (78,"Cancha 7")]:
        partidos = c.execute(text("""
            SELECT id_partido, fecha_hora FROM partidos
            WHERE id_torneo = 38 AND cancha_id = :c AND fecha_hora IS NOT NULL
        """), {"c": cid}).fetchall()
        conflicto = None
        for p in partidos:
            fh = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
            pfin = fh + DURACION
            if hora < pfin and fh < fin:
                conflicto = f"P{p[0]} {fh.strftime('%H:%M')}"
                break
        if conflicto:
            print(f"  ❌ {cname}: ocupada ({conflicto})")
        else:
            print(f"  ✅ {cname}: LIBRE")
