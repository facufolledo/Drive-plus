"""
Desactivar canchas 3, 4 y 5 del torneo 37 (solo quedan 2 techadas)
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

def desactivar_canchas():
    session = Session()
    
    try:
        print("=" * 80)
        print("DESACTIVANDO CANCHAS 3, 4 Y 5 DEL TORNEO 37")
        print("=" * 80)
        
        # Desactivar canchas 3, 4 y 5
        session.execute(
            text("""
                UPDATE torneo_canchas 
                SET activa = false 
                WHERE torneo_id = 37 
                AND nombre IN ('Cancha 3', 'Cancha 4', 'Cancha 5')
            """)
        )
        
        session.commit()
        
        # Verificar
        canchas = session.execute(
            text("SELECT id, nombre, activa FROM torneo_canchas WHERE torneo_id = 37 ORDER BY id")
        ).fetchall()
        
        print(f"\n✅ CANCHAS ACTUALIZADAS:")
        for c in canchas:
            estado = "✅ ACTIVA" if c[2] else "❌ INACTIVA"
            print(f"   • {c[1]}: {estado}")
        
        print(f"\n💡 Ahora regenera el fixture con solo 2 canchas activas")
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    desactivar_canchas()
