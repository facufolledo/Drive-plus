import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    rows = c.execute(text("""
        SELECT p.id_partido, p.estado, p.ganador_pareja_id, p.resultado_padel, p.elo_aplicado,
               p.fecha_hora, p.zona_id, tc.nombre as cancha
        FROM partidos p
        LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id_torneo = 38 AND p.categoria_id = 88
        ORDER BY p.fecha_hora
    """)).fetchall()
    print(f"Partidos 6ta T38: {len(rows)}")
    for r in rows:
        fh = r[5].strftime('%d/%m %H:%M') if r[5] else '?'
        resultado = 'SÍ' if r[3] else 'NO'
        print(f"  P{r[0]} | {fh} | {r[7]} | zona={r[6]} | estado={r[1]} | ganador={r[2]} | resultado={resultado} | elo={r[4]}")
