"""Ver estado de 5ta en torneo 42"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Info del torneo
    t = conn.execute(text("SELECT id, nombre, estado FROM torneos WHERE id = 42")).fetchone()
    print(f"Torneo: {t[0]} - {t[1]} (estado: {t[2]})")
    
    # Categorías del torneo
    cats = conn.execute(text("""
        SELECT id, nombre, genero FROM torneo_categorias WHERE torneo_id = 42 ORDER BY id
    """)).fetchall()
    print(f"\nCategorías:")
    for c in cats:
        print(f"  ID {c[0]}: {c[1]} ({c[2]})")
    
    # Parejas de 5ta
    cat_5ta = [c for c in cats if '5ta' in c[1].lower()]
    if cat_5ta:
        cat_id = cat_5ta[0][0]
        print(f"\nParejas en 5ta (cat_id={cat_id}):")
        parejas = conn.execute(text("""
            SELECT tp.id, tp.estado,
                   p1.nombre || ' ' || p1.apellido as j1,
                   p2.nombre || ' ' || p2.apellido as j2,
                   tp.jugador1_id, tp.jugador2_id
            FROM torneos_parejas tp
            LEFT JOIN perfil_usuarios p1 ON p1.id_usuario = tp.jugador1_id
            LEFT JOIN perfil_usuarios p2 ON p2.id_usuario = tp.jugador2_id
            WHERE tp.torneo_id = 42 AND tp.categoria_id = :cat_id
            ORDER BY tp.id
        """), {"cat_id": cat_id}).fetchall()
        for p in parejas:
            print(f"  Pareja {p[0]}: {p[2]} / {p[3]} (IDs: {p[4]},{p[5]}) - {p[1]}")
        print(f"\nTotal parejas 5ta: {len(parejas)}")
    else:
        print("\nNo hay categoría 5ta en este torneo")
