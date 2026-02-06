"""
Script para actualizar horarios del torneo 37 al formato antiguo (compatible con frontend)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def actualizar_formato():
    session = Session()
    
    try:
        print("=" * 80)
        print("ACTUALIZAR FORMATO HORARIOS TORNEO 37")
        print("=" * 80)
        
        # Formato antiguo (compatible con frontend)
        horarios = {
            "viernes": {"inicio": "15:00", "fin": "23:30"},
            "sabado": {"inicio": "09:00", "fin": "23:30"},
            "domingo": {"inicio": "09:00", "fin": "23:30"}
        }
        
        print(f"\n⏰ Nuevo formato de horarios:")
        for dia, horario in horarios.items():
            print(f"   • {dia}: {horario['inicio']} - {horario['fin']}")
        
        horarios_json = json.dumps(horarios)
        
        session.execute(
            text("""
                UPDATE torneos 
                SET horarios_disponibles = CAST(:horarios AS jsonb)
                WHERE id = 37
            """),
            {"horarios": horarios_json}
        )
        
        session.commit()
        
        print(f"\n✅ Horarios actualizados al formato antiguo (compatible con frontend)")
        print(f"{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    actualizar_formato()
