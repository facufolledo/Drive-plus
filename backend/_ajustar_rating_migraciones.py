"""Ajustar rating de usuarios migrados sumando la diferencia del temp"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# Datos de las migraciones (real_id, rating_original_real, rating_temp_inicio, rating_temp_final, nombre)
ajustes = [
    (504, 1711, 709, 709, "Camilo Nieto"),  # Real 1711, temp 709->709 (sin cambio, ya jugó con el real)
    (80, 1099, 1499, 1100, "Juan Pablo Romero"),  # Real 1099, temp 1499->1100 (perdió 399)
    (232, 1299, 1499, 1674, "Emanuel/Nahuel Toledo"),  # Real 1299, temp 1499->1674 (ganó 175)
    (26, 766, 1499, 1317, "Maxi/Matias Vega"),  # Real 766, temp 1499->1317 (perdió 182)
]

with engine.connect() as conn:
    print("=== AJUSTANDO RATINGS POST-MIGRACIÓN ===\n")
    
    for real_id, rating_real_orig, rating_temp_inicio, rating_temp_final, nombre in ajustes:
        # Calcular diferencia de rating que ganó/perdió el temp
        diferencia_rating = rating_temp_final - rating_temp_inicio
        
        # Aplicar esa diferencia al rating del real
        nuevo_rating = rating_real_orig + diferencia_rating
        
        print(f"{nombre} (ID {real_id}):")
        print(f"  Rating real original: {rating_real_orig}")
        print(f"  Temp: {rating_temp_inicio} -> {rating_temp_final} (Δ {diferencia_rating:+d})")
        print(f"  Nuevo rating real: {rating_real_orig} + {diferencia_rating} = {nuevo_rating}")
        
        # Actualizar rating
        conn.execute(text("""
            UPDATE usuarios 
            SET rating = :rating
            WHERE id_usuario = :uid
        """), {"rating": nuevo_rating, "uid": real_id})
        
        print(f"  ✅ Rating actualizado\n")
    
    conn.commit()
    print("✅ Ajustes completados!")
