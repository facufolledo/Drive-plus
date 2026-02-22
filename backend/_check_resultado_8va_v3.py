import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Partidos 8va no pendientes
    print("=== PARTIDOS 8VA NO PENDIENTES ===")
    rows = c.execute(text("""
        SELECT p.id_partido, p.estado, p.ganador_pareja_id, p.resultado_padel, p.elo_aplicado,
               p.pareja1_id, p.pareja2_id, p.fecha_hora
        FROM partidos p
        WHERE p.id_torneo = 38 AND p.categoria_id = 89 AND p.estado != 'pendiente'
    """)).fetchall()
    if not rows:
        print("  Ninguno - todos pendientes aún")
    for r in rows:
        fh = r[7].replace(tzinfo=None) if r[7].tzinfo else r[7]
        print(f"  P{r[0]} | estado={r[1]} | ganador={r[2]} | resultado={r[3]} | elo_aplicado={r[4]} | pa1={r[5]} pa2={r[6]} | {fh}")
        
        # Jugadores de ambas parejas
        for pid in [r[5], r[6]]:
            tp = c.execute(text("SELECT jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :p"), {"p": pid}).fetchone()
            for jid in [tp[0], tp[1]]:
                u = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :j"), {"j": jid}).fetchone()
                nombre = c.execute(text("SELECT nombre || ' ' || apellido FROM perfil_usuarios WHERE id_usuario = :j"), {"j": jid}).fetchone()[0]
                hist = c.execute(text("SELECT COUNT(*) FROM historial_rating WHERE usuario_id = :j AND partido_id = :p"), {"j": jid, "p": r[0]}).fetchone()[0]
                print(f"    {nombre} (ID {jid}): rating={u[0]}, partidos_jugados={u[1]}, historial={'✅' if hist > 0 else '❌ NO'}")

    # También ver partido_sets
    print("\n=== PARTIDO_SETS DE 8VA T38 ===")
    sets = c.execute(text("""
        SELECT ps.id, ps.partido_id, ps.set_numero, ps.games_pareja1, ps.games_pareja2
        FROM partido_sets ps
        JOIN partidos p ON ps.partido_id = p.id_partido
        WHERE p.id_torneo = 38 AND p.categoria_id = 89
        ORDER BY ps.partido_id, ps.set_numero
    """)).fetchall()
    if not sets:
        print("  Ningún set registrado")
    for s in sets:
        print(f"  Partido P{s[1]} Set {s[2]}: {s[3]}-{s[4]}")
