import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    p = c.execute(text("SELECT id_partido FROM partidos WHERE id_partido = 451")).fetchone()
    print(f"P451 existe: {p is not None}")
    
    # Rango de IDs de partidos T38
    rango = c.execute(text("SELECT MIN(id_partido), MAX(id_partido) FROM partidos WHERE id_torneo = 38")).fetchone()
    print(f"Rango IDs T38: {rango[0]} - {rango[1]}")
    
    # Todos los partidos T38 por categoría
    cats = c.execute(text("""
        SELECT p.categoria_id, tcat.nombre, COUNT(*), 
               SUM(CASE WHEN p.resultado_padel IS NOT NULL THEN 1 ELSE 0 END) as con_resultado
        FROM partidos p
        JOIN torneo_categorias tcat ON p.categoria_id = tcat.id
        WHERE p.id_torneo = 38
        GROUP BY p.categoria_id, tcat.nombre
        ORDER BY p.categoria_id
    """)).fetchall()
    print(f"\nPartidos T38 por categoría:")
    for c2 in cats:
        print(f"  cat {c2[0]} ({c2[1]}): {c2[2]} partidos, {c2[3]} con resultado")
    
    # Historial de P451
    h = c.execute(text("SELECT COUNT(*) FROM historial_rating WHERE id_partido = 451")).fetchone()
    print(f"\nHistorial P451: {h[0]} registros")
