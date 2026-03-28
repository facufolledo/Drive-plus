import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def main():
    s = Session()
    try:
        # Ver columnas de torneos
        cols = s.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'torneos' 
            ORDER BY ordinal_position
        """)).fetchall()
        
        print("Columnas de tabla torneos:")
        print([c[0] for c in cols])
        
        # Ver estado del torneo
        torneo = s.execute(text("""
            SELECT * FROM torneos WHERE id = 45
        """)).fetchone()
        
        print(f"\nTorneo 45:")
        print(f"  Nombre: {torneo[1] if len(torneo) > 1 else 'N/A'}")
        print(f"  Estado: {torneo[6] if len(torneo) > 6 else 'N/A'}")
        
        # Contar partidos
        partidos = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp ON p.pareja1_id = tp.id
            WHERE tp.torneo_id = 45
        """)).scalar()
        
        print(f"\nTotal partidos: {partidos}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
