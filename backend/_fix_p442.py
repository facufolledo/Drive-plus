import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Ver estado actual de P442
    p = c.execute(text("""
        SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.estado, p.ganador_pareja_id,
               p.resultado_padel, p.elo_aplicado, p.fecha_hora, tc.nombre
        FROM partidos p
        LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id_partido = 442
    """)).fetchone()
    print(f"P442: p1={p[1]} p2={p[2]} estado={p[3]} ganador={p[4]}")
    print(f"  resultado={p[5]} elo_aplicado={p[6]}")
    
    # Ver si hay historial de rating generado por P442
    hist = c.execute(text("""
        SELECT h.id_historial, h.id_usuario, h.rating_antes, h.delta, h.rating_despues,
               pu.nombre || ' ' || pu.apellido as nombre
        FROM historial_rating h
        JOIN perfil_usuarios pu ON h.id_usuario = pu.id_usuario
        WHERE h.id_partido = 442
        ORDER BY h.id_historial
    """)).fetchall()
    print(f"\nHistorial rating de P442: {len(hist)} registros")
    for h in hist:
        print(f"  hist {h[0]}: {h[5]} (ID {h[1]}) rating {h[2]} -> {h[4]} (delta {h[3]})")
    
    # Ver ratings actuales de los 4 jugadores de P442
    # P442: pareja 647 (j1=237, j2=79) vs pareja 655 (j1=542, j2=543)
    for uid in [237, 79, 542, 543]:
        u = c.execute(text("""
            SELECT u.id_usuario, u.rating, u.partidos_jugados, pu.nombre || ' ' || pu.apellido
            FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        print(f"  ID {u[0]}: {u[3]} rating={u[1]} partidos={u[2]}")
