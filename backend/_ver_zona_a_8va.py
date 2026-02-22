import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Zonas de 8va (cat 89)
    zonas = c.execute(text("""
        SELECT id, nombre FROM torneo_zonas WHERE torneo_id = 38 AND categoria_id = 89 ORDER BY nombre
    """)).fetchall()
    print("Zonas 8va:")
    for z in zonas:
        print(f"  Zona {z[1]} (ID: {z[0]})")
        # Parejas en la zona
        pzs = c.execute(text("""
            SELECT tzp.pareja_id, p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
            FROM torneo_zona_parejas tzp
            JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
            JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
            JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
            WHERE tzp.zona_id = :z
        """), {"z": z[0]}).fetchall()
        for p in pzs:
            print(f"    Pareja {p[0]}: {p[1]} / {p[2]}")

    # Partidos de 8va
    print("\nPartidos 8va:")
    pts = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, p.pareja1_id, p.pareja2_id, p.zona_id,
               cn.nombre as cancha
        FROM partidos p
        LEFT JOIN torneo_canchas cn ON p.cancha_id = cn.id
        WHERE p.id_torneo = 38 AND p.categoria_id = 89
        ORDER BY p.zona_id, p.fecha_hora
    """)).fetchall()

    # Get pareja names
    parejas = {}
    for r in c.execute(text("""
        SELECT tp.id, p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
        FROM torneos_parejas tp
        JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
        JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
        WHERE tp.torneo_id = 38 AND tp.categoria_id = 89
    """)).fetchall():
        parejas[r[0]] = f"{r[1]}/{r[2]}"

    for p in pts:
        zona_name = "?"
        for z in zonas:
            if z[0] == p[5]:
                zona_name = z[1]
        fecha = p[1].strftime('%a %d/%m %H:%M') if p[1] else "SIN HORA"
        print(f"  Zona {zona_name} | P{p[0]} | {fecha} | {p[6] or '?'} | {parejas.get(p[3],'?')} vs {parejas.get(p[4],'?')}")
