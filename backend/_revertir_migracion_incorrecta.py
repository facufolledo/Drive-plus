"""Revertir migración incorrecta de Juan Loto y Martin Navarro"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# Datos originales antes de la migración
usuarios_revertir = [
    (603, 249, 0, 7, "Juan Loto"),  # rating original, pj original, cat original
    (602, 1499, 0, 7, "Martin Navarro"),
]

with engine.connect() as conn:
    print("=== REVIRTIENDO MIGRACIÓN INCORRECTA ===\n")
    
    for uid, rating_orig, pj_orig, cat_orig, nombre in usuarios_revertir:
        print(f"{nombre} (ID {uid}):")
        
        # Restaurar valores originales
        conn.execute(text("""
            UPDATE usuarios 
            SET rating = :rating, partidos_jugados = :pj, id_categoria = :cat
            WHERE id_usuario = :uid
        """), {"rating": rating_orig, "pj": pj_orig, "cat": cat_orig, "uid": uid})
        
        print(f"  ✅ Restaurado: Rating={rating_orig}, PJ={pj_orig}, Cat={cat_orig}")
    
    conn.commit()
    print("\n✅ Reversión completada")
