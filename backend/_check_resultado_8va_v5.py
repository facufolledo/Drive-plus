import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Historial para jugadores de P445
    jugadores = [538, 539, 540, 541]
    print("=== HISTORIAL_RATING PARA JUGADORES DE P445 ===")
    for jid in jugadores:
        nombre = c.execute(text("SELECT nombre || ' ' || apellido FROM perfil_usuarios WHERE id_usuario = :j"), {"j": jid}).fetchone()[0]
        hist = c.execute(text("SELECT * FROM historial_rating WHERE id_usuario = :j ORDER BY id_historial DESC"), {"j": jid}).fetchall()
        print(f"\n  {nombre} (ID {jid}): {len(hist)} registros")
        for h in hist:
            print(f"    {h}")

    # Ver partido_sets para P445
    print("\n=== PARTIDO_SETS PARA P445 ===")
    sets = c.execute(text("SELECT * FROM partido_sets WHERE partido_id = 445")).fetchall()
    if sets:
        for s in sets:
            print(f"  {s}")
    else:
        print("  ❌ No hay sets registrados")
        # Columnas de partido_sets
        cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'partido_sets'")).fetchall()
        print(f"  Columnas: {[r[0] for r in cols]}")

    # Ver cómo el frontend muestra el historial - buscar endpoint
    print("\n=== ESTADO COMPLETO P445 ===")
    r = c.execute(text("SELECT * FROM partidos WHERE id_partido = 445")).fetchone()
    print(f"  {r}")
