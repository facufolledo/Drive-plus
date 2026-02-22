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
               p2n2.nombre || ' ' || p2n2.apellido as j2p2
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        JOIN torneo_categorias tcat ON p.categoria_id = tcat.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p1n2 ON tp1.jugador2_id = p1n2.id_usuario
        JOIN perfil_usuarios p2n ON tp2.jugador1_id = p2n.id_usuario
        JOIN perfil_usuarios p2n2 ON tp2.jugador2_id = p2n2.id_usuario
        WHERE p.id_torneo = 38 
        AND p.fecha_hora >= '2026-02-20 23:00:00' AND p.fecha_hora < '2026-02-21 00:00:00'
        ORDER BY p.fecha_hora, tc.nombre
    """)).fetchall()
    
    print(f"Partidos a las 23:xx del viernes 20/02:")
    for r in rows:
        fh = r[1].strftime('%H:%M') if r[1] else '?'
        print(f"  P{r[0]} | {fh} | {r[2]} | {r[3]} | {r[4]}/{r[5]} vs {r[6]}/{r[7]}")
    print(f"\n  Total: {len(rows)}")
    
    # Canchas ocupadas a las 23
    print(f"\n  Canchas ocupadas: {set(r[2] for r in rows)}")
    print(f"  Canchas libres: C5={76 not in {r[0] for r in rows}}")
