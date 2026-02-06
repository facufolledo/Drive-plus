"""
Script para verificar el nombre correcto de la tabla de parejas
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

def verificar_tabla_parejas():
    """Verifica el nombre correcto de la tabla de parejas"""
    session = Session()
    
    try:
        print("=" * 80)
        print("VERIFICAR TABLA DE PAREJAS")
        print("=" * 80)
        
        # Buscar tablas relacionadas con parejas
        result = session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%pareja%'
                ORDER BY table_name
            """)
        )
        
        print("\nTablas relacionadas con 'pareja':")
        for row in result:
            print(f"  - {row[0]}")
        
        # Buscar tablas relacionadas con torneos
        result = session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%torneo%'
                ORDER BY table_name
            """)
        )
        
        print("\nTablas relacionadas con 'torneo':")
        for row in result:
            print(f"  - {row[0]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verificar_tabla_parejas()
