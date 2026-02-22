import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Columnas historial_rating
    cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'historial_rating' ORDER BY ordinal_position")).fetchall()
    print("Columnas historial_rating:", [r[0] for r in cols])

    # P445: Rodríguez/Castelli (653) vs Pérez/Rodríguez (654), ganador=654, elo_aplicado=True
    print("\n=== P445 - RESULTADO CARGADO ===")
    print("Rodríguez/Castelli (PA653) 3-6 1-6 Pérez/Rodríguez (PA654)")
    print("Ganador: PA654, elo_aplicado: True")

    # Jugadores de ambas parejas
    for pid, nombre_p in [(653, "Rodríguez/Castelli"), (654, "Pérez/Rodríguez")]:
        tp = c.execute(text("SELECT jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :p"), {"p": pid}).fetchone()
        print(f"\n  Pareja {pid} ({nombre_p}):")
        for jid in [tp[0], tp[1]]:
            u = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :j"), {"j": jid}).fetchone()
            nombre = c.execute(text("SELECT nombre || ' ' || apellido FROM perfil_usuarios WHERE id_usuario = :j"), {"j": jid}).fetchone()[0]
            print(f"    {nombre} (ID {jid}): rating={u[0]}, partidos_jugados={u[1]}")

    # Buscar en historial_rating para partido 445
    print("\n=== HISTORIAL_RATING PARA P445 ===")
    # Primero ver qué columna tiene el partido
    hist = c.execute(text("SELECT * FROM historial_rating WHERE partido_id = 445")).fetchall()
    if hist:
        for h in hist:
            print(f"  {h}")
    else:
        print("  ❌ No hay registros de historial_rating para P445")
        # Ver últimos registros
        print("\n  Últimos 5 registros de historial_rating:")
        last = c.execute(text("SELECT * FROM historial_rating ORDER BY id DESC LIMIT 5")).fetchall()
        for l in last:
            print(f"    {l}")
