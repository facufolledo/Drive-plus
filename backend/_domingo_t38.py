import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, tc.nombre as cancha, tcat.nombre as categoria,
               p1n.nombre || ' ' || p1n.apellido || ' / ' || p2n.nombre || ' ' || p2n.apellido as pareja1,
               p3n.nombre || ' ' || p3n.apellido || ' / ' || p4n.nombre || ' ' || p4n.apellido as pareja2
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        JOIN torneo_categorias tcat ON p.categoria_id = tcat.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
        JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
        WHERE p.id_torneo = 38 AND p.fecha_hora::date = '2026-02-22'
        ORDER BY p.fecha_hora, tc.nombre
    """)).fetchall()
    if rows:
        for r in rows:
            fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
            print(f"P{r[0]} | {fh.strftime('%H:%M')} | {r[2]} | {r[3]} | {r[4]} vs {r[5]}")
    else:
        print("No hay partidos el domingo 22/02")
