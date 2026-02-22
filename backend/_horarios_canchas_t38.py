"""Listar horas ocupadas por cancha en torneo 38, agrupadas por día y cancha"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    rows = c.execute(text("""
        SELECT p.fecha_hora, tc.nombre as cancha
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id_torneo = 38 AND p.fecha_hora IS NOT NULL
        ORDER BY tc.nombre, p.fecha_hora
    """)).fetchall()

    from collections import defaultdict
    # cancha -> dia -> [horas]
    data = defaultdict(lambda: defaultdict(list))
    for r in rows:
        fh = r[0].replace(tzinfo=None) if r[0].tzinfo else r[0]
        dia = fh.strftime("%A %d/%m").replace("Friday", "Viernes").replace("Saturday", "Sábado").replace("Sunday", "Domingo")
        hora = fh.strftime("%H:%M")
        data[r[1]][dia].append(hora)

    for cancha in sorted(data.keys()):
        print(f"\n{'='*40}")
        print(f"  {cancha}")
        print(f"{'='*40}")
        for dia in sorted(data[cancha].keys(), key=lambda d: d.split()[1]):
            horas = sorted(data[cancha][dia])
            print(f"  {dia}: {', '.join(horas)}")
