import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Ver P424 (Palacio vs Palma sáb 15:00) y P441
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.fecha, p.cancha_id, tc.nombre,
               p1n.nombre || ' ' || p1n.apellido || ' / ' || p2n.nombre || ' ' || p2n.apellido as pareja1,
               p3n.nombre || ' ' || p3n.apellido || ' / ' || p4n.nombre || ' ' || p4n.apellido as pareja2,
               p.zona_id
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
        JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
        WHERE p.id_partido IN (424, 441)
        ORDER BY p.id_partido
    """)).fetchall()
    for r in rows:
        fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
        fecha = r[2]
        print(f"P{r[0]} | fecha_hora={fh} | fecha={fecha} | {r[4]} | zona={r[7]} | {r[5]} vs {r[6]}")

    # También buscar todos los partidos de Palacio/Porras (655) y Palma/Tapia (657)
    print("\n--- Todos los partidos de parejas 655 y 657 ---")
    rows2 = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, tc.nombre,
               p.pareja1_id, p.pareja2_id, p.zona_id
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id_torneo = 38 AND (p.pareja1_id IN (655,657) OR p.pareja2_id IN (655,657))
        ORDER BY p.fecha_hora
    """)).fetchall()
    for r in rows2:
        fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
        print(f"P{r[0]} | {fh} | {r[3]} | p1={r[4]} p2={r[5]} | zona={r[6]}")
