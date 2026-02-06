"""
Script para buscar dónde están los partidos del torneo 37
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

def buscar_partidos():
    session = Session()
    
    try:
        print("Buscando partidos del torneo 37...")
        print("=" * 60)
        
        # Buscar tablas con 'partido' en el nombre
        result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%partido%'
            ORDER BY table_name
        """))
        
        print("\nTablas con 'partido':")
        for row in result:
            table = row[0]
            try:
                count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  {table}: {count} registros")
            except Exception as e:
                print(f"  {table}: Error - {e}")
        
        # Verificar torneo_partido_sets
        sets = session.execute(text("""
            SELECT COUNT(*) FROM torneo_partido_sets
        """)).scalar()
        print(f"\ntorneo_partido_sets: {sets}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    buscar_partidos()
