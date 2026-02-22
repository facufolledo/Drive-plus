import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Ver columnas de partidos
    cols = c.execute(text("""
        SELECT column_name FROM information_schema.columns WHERE table_name = 'partidos' ORDER BY ordinal_position
    """)).fetchall()
    print("Columnas partidos:", [r[0] for r in cols])

    # Partidos 8va no pendientes
    print("\n=== PARTIDOS 8VA NO PENDIENTES ===")
    rows = c.execute(text("""
        SELECT p.id_partido, p.estado, p.ganador_id, p.fecha_hora, p.pareja1_id, p.pareja2_id
        FROM partidos p
        WHERE p.id_torneo = 38 AND p.categoria_id = 89 AND p.estado != 'pendiente'
    """)).fetchall()
    if not rows:
        print("  Ninguno - todos pendientes")
    for r in rows:
        print(f"  P{r[0]} estado={r[1]} ganador={r[2]} pa1={r[4]} pa2={r[5]}")

    # Buscar en partido_sets si existe
    print("\n=== TABLAS RELACIONADAS A RESULTADOS ===")
    tables = c.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND (table_name LIKE '%set%' OR table_name LIKE '%result%' OR table_name LIKE '%historial%')
    """)).fetchall()
    for t in tables:
        print(f"  {t[0]}")

    # Ver historial_rating recientes
    print("\n=== ÚLTIMOS HISTORIAL_RATING ===")
    hist = c.execute(text("""
        SELECT id, usuario_id, partido_id, rating_anterior, rating_nuevo, created_at
        FROM historial_rating ORDER BY id DESC LIMIT 5
    """)).fetchall()
    for h in hist:
        print(f"  id={h[0]} user={h[1]} partido={h[2]} {h[3]}->{h[4]} {h[5]}")

    # Ver partido_sets
    print("\n=== PARTIDO_SETS DE 8VA T38 ===")
    try:
        sets = c.execute(text("""
            SELECT ps.* FROM partido_sets ps
            JOIN partidos p ON ps.partido_id = p.id_partido
            WHERE p.id_torneo = 38 AND p.categoria_id = 89
        """)).fetchall()
        for s in sets:
            print(f"  {s}")
    except Exception as e:
        print(f"  Error: {e}")
