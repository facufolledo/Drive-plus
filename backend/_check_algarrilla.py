import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Parejas de Algarrilla
    rows = c.execute(text("""
        SELECT tp.id, tp.torneo_id, tp.categoria_id, tcat.nombre, tp.jugador1_id, tp.jugador2_id
        FROM torneos_parejas tp
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        WHERE tp.jugador1_id = 491 OR tp.jugador2_id = 491
    """)).fetchall()
    for r in rows:
        print(r)
