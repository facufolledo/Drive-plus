"""
Actualizar canchas del torneo 37 - Solo 2 canchas techadas disponibles
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

def actualizar_canchas():
    """Desactiva canchas 3, 4 y 5 - Solo quedan 2 techadas"""
    session = Session()
    
    try:
        print("=" * 80)
        print("ACTUALIZANDO CANCHAS DEL TORNEO 37")
        print("=" * 80)
        
        # Desactivar canchas 3, 4 y 5
        result = session.execute(
            text("""
                UPDATE torneo_canchas
                SET activa = false
                WHERE torneo_id = 37
                AND nombre IN ('Cancha 3', 'Cancha 4', 'Cancha 5')
                RETURNING id, nombre
            """)
        )
        
        canchas_desactivadas = result.fetchall()
        session.commit()
        
        print(f"\n✅ Canchas desactivadas: {len(canchas_desactivadas)}")
        for cancha in canchas_desactivadas:
            print(f"   • {cancha[1]}")
        
        # Verificar estado actual
        canchas_activas = session.execute(
            text("""
                SELECT id, nombre, activa
                FROM torneo_canchas
                WHERE torneo_id = 37
                ORDER BY nombre
            """)
        ).fetchall()
        
        print(f"\n📊 ESTADO ACTUAL DE CANCHAS:")
        for cancha in canchas_activas:
            estado = "✅ Activa (techada)" if cancha[2] else "❌ Inactiva"
            print(f"   • {cancha[1]}: {estado}")
        
        print(f"\n💡 Solo 2 canchas techadas disponibles para el torneo")
        print(f"   Esto afectará la generación del fixture (menos slots simultáneos)")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    actualizar_canchas()
