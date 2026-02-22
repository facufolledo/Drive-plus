import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Columnas de torneos_parejas
    cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='torneos_parejas' ORDER BY ordinal_position")).fetchall()
    print("Columnas torneos_parejas:", [c[0] for c in cols])
    
    # Zonas 8va T38
    zonas = c.execute(text("""
        SELECT z.id, z.nombre, z.numero_orden FROM torneo_zonas z
        WHERE z.torneo_id = 38 AND z.categoria_id = 89
        ORDER BY z.numero_orden
    """)).fetchall()
    print("\nZonas 8va T38:")
    for z in zonas:
        print(f"  ID {z[0]}: {z[1]} (orden {z[2]})")
        parejas = c.execute(text("""
            SELECT tp.id, tp.estado, tp.jugador1_id, tp.jugador2_id,
                   p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
            FROM torneo_zona_parejas tzp
            JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
            LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
            WHERE tzp.zona_id = :zid
        """), {"zid": z[0]}).fetchall()
        for p in parejas:
            print(f"    Pareja {p[0]}: {p[4]} / {p[5]} ({p[1]}) j1={p[2]} j2={p[3]}")
    
    # Partidos 8va
    partidos = c.execute(text("""
        SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.fecha_hora, tc.nombre, p.estado, p.fase
        FROM partidos p
        LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id_torneo = 38 AND p.categoria_id = 89
        ORDER BY p.fecha_hora
    """)).fetchall()
    print(f"\nPartidos 8va T38: {len(partidos)}")
    for p in partidos:
        fh = p[3].strftime('%d/%m %H:%M') if p[3] else '?'
        print(f"  P{p[0]}: p1={p[1]} vs p2={p[2]} | {fh} | {p[4]} | {p[5]} | {p[6]}")
    
    # Temp nuevos
    for uid in ['tiago.cordoba.8va', 'camilo.nieto.8va']:
        u = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria, p.nombre, p.apellido
            FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.nombre_usuario = :u
        """), {"u": uid}).fetchone()
        if u:
            print(f"\n  {u[4]} {u[5]}: ID {u[0]}, rating={u[2]}, cat={u[3]}")
