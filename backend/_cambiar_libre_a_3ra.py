"""Cambiar categoría 'Libre' por '3ra' en la base de datos"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("=== CAMBIANDO 'Libre' POR '3ra' ===\n")
    
    # Verificar categoría actual
    result = conn.execute(text("""
        SELECT id_categoria, nombre 
        FROM categorias 
        WHERE id_categoria = 6
    """)).fetchone()
    
    print(f"Categoría actual: ID={result[0]}, Nombre='{result[1]}'")
    
    # Actualizar nombre
    conn.execute(text("""
        UPDATE categorias 
        SET nombre = '3ra'
        WHERE id_categoria = 6
    """))
    
    conn.commit()
    
    # Verificar cambio
    result = conn.execute(text("""
        SELECT id_categoria, nombre 
        FROM categorias 
        WHERE id_categoria = 6
    """)).fetchone()
    
    print(f"Categoría actualizada: ID={result[0]}, Nombre='{result[1]}'")
    print(f"\n✅ Cambio completado en la base de datos!")
