import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # P465 zona_id es NULL, debería ser 208 (Zona E de 8va)
    c.execute(text("UPDATE partidos SET zona_id = 208 WHERE id_partido = 465"))
    c.commit()
    
    # Verificar todos los partidos T38 sin zona_id
    sin_zona = c.execute(text("""
        SELECT id_partido, categoria_id, pareja1_id, pareja2_id, fase
        FROM partidos WHERE id_torneo = 38 AND zona_id IS NULL
    """)).fetchall()
    print(f"Partidos T38 sin zona_id: {len(sin_zona)}")
    for p in sin_zona:
        print(f"  P{p[0]} cat={p[1]} p1={p[2]} p2={p[3]} fase={p[4]}")
