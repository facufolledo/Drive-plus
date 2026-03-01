"""Actualizar todos los registros de historial_rating que mencionen 'Libre' por '3ra'"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("=== ACTUALIZANDO HISTORIAL_RATING: 'Libre' → '3ra' ===\n")
    
    # Buscar registros con "Libre" en cambio_categoria
    registros = conn.execute(text("""
        SELECT id_historial, cambio_categoria
        FROM historial_rating
        WHERE cambio_categoria LIKE '%Libre%'
    """)).fetchall()
    
    print(f"Registros encontrados con 'Libre': {len(registros)}\n")
    
    if len(registros) == 0:
        print("✅ No hay registros para actualizar")
    else:
        # Actualizar cada registro
        for registro in registros:
            id_hist, cambio_cat = registro
            nuevo_cambio = cambio_cat.replace('Libre', '3ra')
            
            conn.execute(text("""
                UPDATE historial_rating
                SET cambio_categoria = :nuevo
                WHERE id_historial = :id
            """), {"nuevo": nuevo_cambio, "id": id_hist})
            
            print(f"ID {id_hist}:")
            print(f"  Antes: {cambio_cat}")
            print(f"  Después: {nuevo_cambio}\n")
        
        conn.commit()
        print(f"✅ {len(registros)} registros actualizados!")
