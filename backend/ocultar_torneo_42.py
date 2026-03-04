"""
Script para ocultar el torneo 42 (sin borrarlo)
Cambia el estado a 'oculto' para que no aparezca en listados públicos
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

from src.models.torneo_models import Torneo

def ocultar_torneo_42():
    db = SessionLocal()
    try:
        torneo_id = 42
        
        print(f"🔍 Buscando torneo {torneo_id}...")
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        
        if not torneo:
            print(f"❌ Torneo {torneo_id} no encontrado")
            return
        
        print(f"✅ Torneo encontrado: {torneo.nombre}")
        print(f"   Estado actual: {torneo.estado}")
        
        # Guardar estado anterior
        estado_anterior = torneo.estado
        
        # Cambiar a estado 'oculto'
        torneo.estado = 'oculto'
        
        db.commit()
        
        print(f"\n✅ Torneo ocultado exitosamente")
        print(f"   Estado anterior: {estado_anterior}")
        print(f"   Estado nuevo: {torneo.estado}")
        print(f"\n💡 El torneo ya no aparecerá en listados públicos")
        print(f"   pero todos sus datos se mantienen intactos.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    ocultar_torneo_42()
