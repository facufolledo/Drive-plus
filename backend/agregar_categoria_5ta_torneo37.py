"""
Script para agregar categoría 5ta al torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def agregar_categoria_5ta():
    """Agrega categoría 5ta al torneo 37"""
    session = Session()
    
    try:
        print("=" * 80)
        print("AGREGAR CATEGORÍA 5TA AL TORNEO 37")
        print("=" * 80)
        
        # Verificar si ya existe
        existe = session.execute(
            text("""
                SELECT id FROM torneo_categorias 
                WHERE torneo_id = 37 AND nombre = '5ta'
            """)
        ).fetchone()
        
        if existe:
            print(f"\n⚠️  La categoría 5ta ya existe (ID: {existe[0]})")
            return
        
        # Crear categoría
        result = session.execute(
            text("""
                INSERT INTO torneo_categorias (torneo_id, nombre, genero, max_parejas, orden)
                VALUES (37, '5ta', 'masculino', 999, 2)
                RETURNING id
            """)
        )
        
        cat_id = result.fetchone()[0]
        session.commit()
        
        print(f"\n✅ Categoría 5ta creada exitosamente")
        print(f"   ID: {cat_id}")
        print(f"   Torneo: 37")
        print(f"   Género: masculino")
        print(f"   Max parejas: 999")
        
        print(f"\n{'=' * 80}")
        print("✅ CATEGORÍA AGREGADA")
        print(f"{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    agregar_categoria_5ta()
