"""
Script para buscar la tabla de perfil de usuario
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

def buscar_tabla_perfil():
    """Busca la tabla de perfil de usuario"""
    session = Session()
    
    try:
        # Buscar tablas relacionadas con usuario
        result = session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%usuario%'
                ORDER BY table_name
            """)
        )
        
        print("Tablas relacionadas con 'usuario':")
        for row in result:
            print(f"  - {row[0]}")
        
        # Buscar columnas de la tabla usuarios
        result = session.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_name = 'usuarios'
                ORDER BY ordinal_position
            """)
        )
        
        print("\nColumnas de la tabla 'usuarios':")
        for row in result:
            print(f"  - {row[0]}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    buscar_tabla_perfil()
