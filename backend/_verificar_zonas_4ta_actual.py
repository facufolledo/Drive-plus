"""Verificar estado actual completo de zonas y partidos 4ta"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

print("=== ZONAS Y PAREJAS 4ta ===\n")
zonas = s.execute(text(
    "SELECT z.id, z.nombre FROM torneo_zonas z WHERE z.torneo_id = 38 AND z.categoria_id = 87 ORDER BY z.nombre"
)).fetchall()

for zona in zonas:
    parejas = s.execute(text(
        "SELECT zp.pareja_id FROM torneo_zona_parejas zp WHERE zp.zona_id = :zid ORDER BY zp.pareja_id"
    ), {"zid": zona[0]}).fetchall()
    pareja_ids = [p[0] for p in parejas]
    
    print(f"{zona[1]} (ID {zona[0]}): parejas {pareja_ids}")
    for pid in pareja_ids:
        p = s.execute(text(
            "SELECT tp.id, p1.nombre, p1.apellido, p2.nombre, p2.apellido "
            "FROM torneos_parejas tp "
            "LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario "
            "LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario "
            "WHERE tp.id = :pid"
        ), {"pid": pid}).fetchone()
        print(f"  {p[0]}: {p[1]} {p[2]} / {p[3]} {p[4]}")

print("\n=== PARTIDOS 4ta (con nombres) ===\n")
partidos = s.execute(text("""
    SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.fecha_hora, p.cancha_id, p.zona_id,
           z.nombre as zona_nombre, c.nombre as cancha_nombre
    FROM partidos p
    LEFT JOIN torneo_zonas z ON p.zona_id = z.id
    LEFT JOIN torneo_canchas c ON p.cancha_id = c.id
    WHERE p.id_torneo = 38 AND p.categoria_id = 87 AND p.fase = 'zona'
    ORDER BY z.nombre, p.fecha_hora
""")).fetchall()

for p in partidos:
    # Get pareja names
    p1 = s.execute(text(
        "SELECT pf1.apellido, pf2.apellido FROM torneos_parejas tp "
        "LEFT JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario "
        "LEFT JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario "
        "WHERE tp.id = :pid"
    ), {"pid": p[1]}).fetchone()
    p2 = s.execute(text(
        "SELECT pf1.apellido, pf2.apellido FROM torneos_parejas tp "
        "LEFT JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario "
        "LEFT JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario "
        "WHERE tp.id = :pid"
    ), {"pid": p[2]}).fetchone()
    
    fecha = p[3].strftime('%a %d/%m %H:%M') if p[3] else 'SIN HORA'
    print(f"{p[6]} | {fecha} | {p1[0]}/{p1[1]} vs {p2[0]}/{p2[1]} | {p[7]} | partido {p[0]}")

s.close()
