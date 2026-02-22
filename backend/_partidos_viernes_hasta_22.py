import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, tc.nombre as cancha, tcat.nombre as cat,
               p1n.nombre || ' ' || p1n.apellido as j1p1,
               p1n2.nombre || ' ' || p1n2.apellido as j2p1,
               p2n.nombre || ' ' || p2n.apellido as j1p2,
               p2n2.nombre || ' ' || p2n2.apellido as j2p2,
               p.estado, p.ganador_pareja_id
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        JOIN torneo_categorias tcat ON p.categoria_id = tcat.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p1n2 ON tp1.jugador2_id = p1n2.id_usuario
        JOIN perfil_usuarios p2n ON tp2.jugador1_id = p2n.id_usuario
        JOIN perfil_usuarios p2n2 ON tp2.jugador2_id = p2n2.id_usuario
        WHERE p.id_torneo = 38 AND p.fecha_hora IS NOT NULL
        AND p.fecha_hora <= '2026-02-20 22:00:00'
        ORDER BY p.fecha_hora, tc.nombre
    """)).fetchall()
    
    for r in rows:
        fh = r[1].strftime('%a %d %H:%M') if r[1] else '?'
        ganador = "✅" if r[9] else "⏳"
        print(f"  P{r[0]} | {fh} | {r[2]} | {r[3]} | {r[4]}/{r[5]} vs {r[6]}/{r[7]} | {ganador}")
    
    print(f"\n  Total: {len(rows)} partidos hasta vie 22:00")
    con_resultado = sum(1 for r in rows if r[9])
    print(f"  Con resultado: {con_resultado}, Sin resultado: {len(rows) - con_resultado}")
