import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    r = c.execute(text("SELECT id_partido, tipo, estado, elo_aplicado FROM partidos WHERE id_partido = 445")).fetchone()
    print(f"P445: tipo='{r[1]}', estado='{r[2]}', elo_aplicado={r[3]}")

    # Simular el query del endpoint
    print("\n=== SIMULANDO QUERY DEL ENDPOINT PARA USUARIO 540 (Maximiliano Pérez) ===")
    rows = c.execute(text("""
        SELECT DISTINCT hr.id_partido 
        FROM historial_rating hr
        JOIN partidos p ON hr.id_partido = p.id_partido
        WHERE hr.id_usuario = 540
        AND p.tipo = 'torneo'
        AND p.estado IN ('confirmado', 'finalizado')
    """)).fetchall()
    print(f"  Partidos encontrados: {[r[0] for r in rows]}")

    # Sin filtro de tipo
    print("\n=== SIN FILTRO DE TIPO ===")
    rows2 = c.execute(text("""
        SELECT DISTINCT hr.id_partido, p.tipo, p.estado
        FROM historial_rating hr
        JOIN partidos p ON hr.id_partido = p.id_partido
        WHERE hr.id_usuario = 540
    """)).fetchall()
    for r in rows2:
        print(f"  P{r[0]}: tipo='{r[1]}', estado='{r[2]}'")
