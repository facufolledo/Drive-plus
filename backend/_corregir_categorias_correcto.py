"""Corregir categorías de TODOS los usuarios según su rating (RANGOS CORRECTOS)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# Rangos CORRECTOS de categorías según rating
def obtener_categoria_por_rating(rating):
    """
    Principiante: 7 (0-499)
    8va: 1 (500-999)
    7ma: 2 (1000-1199)
    6ta: 3 (1200-1399)
    5ta: 4 (1400-1599)
    4ta: 5 (1600-1799)
    Libre: 6 (1800+)
    """
    if rating < 500:
        return 7  # Principiante
    elif rating < 1000:
        return 1  # 8va
    elif rating < 1200:
        return 2  # 7ma
    elif rating < 1400:
        return 3  # 6ta
    elif rating < 1600:
        return 4  # 5ta
    elif rating < 1800:
        return 5  # 4ta
    else:
        return 6  # Libre

nombres_categorias = {
    7: "Principiante",
    1: "8va",
    2: "7ma",
    3: "6ta",
    4: "5ta",
    5: "4ta",
    6: "Libre"
}

with engine.connect() as conn:
    print("=== CORRIGIENDO CATEGORÍAS (RANGOS CORRECTOS) ===\n")
    
    # Obtener todos los usuarios
    usuarios = conn.execute(text("""
        SELECT id_usuario, rating, id_categoria
        FROM usuarios
        ORDER BY id_usuario
    """)).fetchall()
    
    print(f"Total usuarios: {len(usuarios)}\n")
    
    actualizados = 0
    sin_cambios = 0
    
    for usuario in usuarios:
        uid, rating, cat_actual = usuario
        cat_correcta = obtener_categoria_por_rating(rating)
        
        if cat_actual != cat_correcta:
            # Actualizar categoría
            conn.execute(text("""
                UPDATE usuarios 
                SET id_categoria = :cat
                WHERE id_usuario = :uid
            """), {"cat": cat_correcta, "uid": uid})
            
            print(f"Usuario {uid}: Rating {rating} - {nombres_categorias.get(cat_actual, '?')} -> {nombres_categorias[cat_correcta]}")
            actualizados += 1
        else:
            sin_cambios += 1
    
    conn.commit()
    
    print(f"\n=== RESUMEN ===")
    print(f"Actualizados: {actualizados}")
    print(f"Sin cambios: {sin_cambios}")
    print(f"\n✅ Corrección completada!")
