#!/usr/bin/env python3
"""
Fix solapamiento: mover partido 762 al jueves 23:00 Cancha 3
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

def fix():
    s = Session()
    try:
        print("Moviendo partido 762 al jueves 23:00 Cancha 3...")
        
        # Mover partido 762 al jueves 05/03 23:00 Cancha 3 (ID 91)
        s.execute(text("""
            UPDATE partidos
            SET fecha_hora = '2026-03-05 23:00:00', cancha_id = 91
            WHERE id_partido = 762
        """))
        
        s.commit()
        print("✅ Partido 762 movido al jueves 05/03 23:00 Cancha 3")
        
    except Exception as e:
        s.rollback()
        print(f"❌ Error: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    fix()
