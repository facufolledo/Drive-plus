import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Zona 202 - todos los partidos
    print("=== ZONA 202 (Zona A 8va) - TODOS LOS PARTIDOS ===")
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, tc.nombre,
               p.pareja1_id, p.pareja2_id,
               p1n.nombre || ' ' || p1n.apellido || '/' || p2n.nombre || ' ' || p2n.apellido,
               p3n.nombre || ' ' || p3n.apellido || '/' || p4n.nombre || ' ' || p4n.apellido
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
        JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
        WHERE p.zona_id = 202
        ORDER BY p.fecha_hora
    """)).fetchall()
    for r in rows:
        fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
        print(f"  P{r[0]} | {fh.strftime('%a %d/%m %H:%M')} | {r[3]} | PA{r[4]} vs PA{r[5]} | {r[6]} vs {r[7]}")

    # Verificar si P424, P425, P426 existen
    print("\n=== P424, P425, P426 ===")
    for pid in [424, 425, 426]:
        r = c.execute(text("SELECT id_partido, fecha_hora, cancha_id, zona_id, pareja1_id, pareja2_id FROM partidos WHERE id_partido = :p"), {"p": pid}).fetchone()
        if r:
            fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
            print(f"  P{r[0]} | {fh} | cancha={r[2]} | zona={r[3]} | p1={r[4]} p2={r[5]}")
        else:
            print(f"  P{pid} NO EXISTE")
