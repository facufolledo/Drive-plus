import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    p = c.execute(text("""
        SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.estado, p.ganador_pareja_id,
               p.resultado_padel, p.elo_aplicado, p.fecha_hora, tc.nombre, p.categoria_id
        FROM partidos p
        LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id_partido = 451
    """)).fetchone()
    print(f"P451: p1={p[1]} p2={p[2]} estado={p[3]} ganador={p[4]} cat={p[9]}")
    print(f"  resultado={p[5]}")
    print(f"  elo_aplicado={p[6]} fecha={p[7]} cancha={p[8]}")
    
    for pid in [p[1], p[2]]:
        par = c.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
                   p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
            FROM torneos_parejas tp
            JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
            JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
            WHERE tp.id = :pid
        """), {"pid": pid}).fetchone()
        print(f"  Pareja {par[0]}: {par[3]} / {par[4]} (j1={par[1]} j2={par[2]})")
    
    # Historial
    hist = c.execute(text("""
        SELECT h.id_historial, h.id_usuario, h.rating_antes, h.delta, h.rating_despues,
               pu.nombre || ' ' || pu.apellido
        FROM historial_rating h
        JOIN perfil_usuarios pu ON h.id_usuario = pu.id_usuario
        WHERE h.id_partido = 451
        ORDER BY h.id_historial
    """)).fetchall()
    print(f"\nHistorial P451: {len(hist)} registros")
    for h in hist:
        print(f"  {h[5]} (ID {h[1]}): {h[2]} -> {h[4]} (delta {h[3]})")
    
    # Buscar Leandro Ruarte
    ruarte = c.execute(text("""
        SELECT u.id_usuario, pu.nombre, pu.apellido
        FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
        WHERE pu.apellido ILIKE '%ruarte%'
    """)).fetchall()
    print(f"\nLeandro Ruarte encontrados: {ruarte}")
