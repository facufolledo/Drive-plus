import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Partidos de 8va con resultado cargado
    print("=== PARTIDOS 8VA CON RESULTADO ===")
    rows = c.execute(text("""
        SELECT p.id_partido, p.estado, p.resultado_pareja1, p.resultado_pareja2,
               p.ganador_id, p.fecha_hora,
               p1n.nombre || ' ' || p1n.apellido || '/' || p2n.nombre || ' ' || p2n.apellido as pa1,
               p3n.nombre || ' ' || p3n.apellido || '/' || p4n.nombre || ' ' || p4n.apellido as pa2,
               p.pareja1_id, p.pareja2_id
        FROM partidos p
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
        JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
        WHERE p.id_torneo = 38 AND p.categoria_id = 89 AND p.estado != 'pendiente'
        ORDER BY p.fecha_hora
    """)).fetchall()
    for r in rows:
        fh = r[5].replace(tzinfo=None) if r[5].tzinfo else r[5]
        print(f"  P{r[0]} | {r[1]} | {r[2]}-{r[3]} | ganador={r[4]} | {r[6]} vs {r[7]}")
        # Check jugadores de ambas parejas
        for pid_label, pid in [("PA1", r[8]), ("PA2", r[9])]:
            tp = c.execute(text("SELECT jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :p"), {"p": pid}).fetchone()
            for jid in [tp[0], tp[1]]:
                u = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :j"), {"j": jid}).fetchone()
                nombre = c.execute(text("SELECT nombre || ' ' || apellido FROM perfil_usuarios WHERE id_usuario = :j"), {"j": jid}).fetchone()[0]
                # Check historial_rating
                hist = c.execute(text("""
                    SELECT COUNT(*) FROM historial_rating WHERE usuario_id = :j AND partido_id = :p
                """), {"j": jid, "p": r[0]}).fetchone()[0]
                print(f"    {pid_label} {nombre} (ID {jid}): rating={u[0]}, partidos={u[1]}, historial={'✅' if hist > 0 else '❌ NO'}")

    if not rows:
        print("  Ningún partido con resultado aún")
        # Buscar en todos los estados
        print("\n=== ESTADOS DE PARTIDOS 8VA ===")
        estados = c.execute(text("""
            SELECT estado, COUNT(*) FROM partidos WHERE id_torneo = 38 AND categoria_id = 89 GROUP BY estado
        """)).fetchall()
        for e in estados:
            print(f"  {e[0]}: {e[1]}")
