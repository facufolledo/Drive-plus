"""
Script para verificar las columnas de la tabla torneos_parejas
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

def verificar_columnas():
    """Verifica las columnas de la tabla torneos_parejas"""
    session = Session()
    
    try:
        print("=" * 80)
        print("COLUMNAS DE LA TABLA torneos_parejas")
        print("=" * 80)
        
        result = session.execute(
            text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'torneos_parejas'
                ORDER BY ordinal_position
            """)
        )
        
        print("\nColumnas:")
        for column_name, data_type, is_nullable in result:
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            print(f"  - {column_name:30} {data_type:20} {nullable}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verificar_columnas()
