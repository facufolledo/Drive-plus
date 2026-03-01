"""Verificar que los temps del T42 tengan rating y categoría correctos"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Temps creados para T42 (IDs 583-593)
    temps = conn.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria, c.nombre as cat_nombre
        FROM usuarios u
        JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        LEFT JOIN categorias c ON c.id_categoria = u.id_categoria
        WHERE u.id_usuario BETWEEN 583 AND 593
        ORDER BY u.id_usuario
    """)).fetchall()
    
    print("=== TEMPS CREADOS PARA T42 ===")
    for t in temps:
        print(f"  ID {t[0]}: {t[1]} {t[2]} -> rating:{t[3]}, cat:{t[4]} ({t[5]})")
    
    # Ver en qué categoría están inscritos
    print("\n=== INSCRIPCIONES ===")
    inscripciones = conn.execute(text("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tc.nombre as cat_nombre, tc.id
        FROM torneos_parejas tp
        JOIN torneo_categorias tc ON tc.id = tp.categoria_id
        WHERE tp.torneo_id = 42
          AND (tp.jugador1_id BETWEEN 583 AND 593 OR tp.jugador2_id BETWEEN 583 AND 593)
        ORDER BY tp.id
    """)).fetchall()
    for i in inscripciones:
        print(f"  Pareja {i[0]}: j1={i[1]}, j2={i[2]} -> cat: {i[3]} (cat_id={i[4]})")

print("\n✅ Verificación completa")
