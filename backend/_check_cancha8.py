import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id,
               p.pareja1_id, p.pareja2_id, p.categoria_id, p.zona_id,
               p1n.nombre || ' ' || p1n.apellido || '/' || p2n.nombre || ' ' || p2n.apellido,
               p3n.nombre || ' ' || p3n.apellido || '/' || p4n.nombre || ' ' || p4n.apellido
        FROM partidos p
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
        JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
        WHERE p.id_torneo = 38 AND p.cancha_id = 79
        ORDER BY p.fecha_hora
    """)).fetchall()
    print("=== PARTIDOS EN CANCHA 8 (ID 79) ===")
    for r in rows:
        fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
        print(f"  P{r[0]} | {fh.strftime('%a %d/%m %H:%M')} | cat={r[5]} zona={r[6]} | {r[7]} vs {r[8]}")
