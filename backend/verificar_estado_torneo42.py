"""
Script para verificar el estado actual del torneo 42 en producción
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Cargar variables de producción
load_dotenv('.env.production')

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

from src.models.torneo_models import Torneo

def verificar_estado():
    db = SessionLocal()
    try:
        torneo_id = 42
        
        print(f"🔍 Verificando torneo {torneo_id} en PRODUCCIÓN...")
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        
        if not torneo:
            print(f"❌ Torneo {torneo_id} no encontrado")
            return
        
        print(f"\n✅ Torneo encontrado:")
        print(f"   ID: {torneo.id}")
        print(f"   Nombre: {torneo.nombre}")
        print(f"   Estado: {torneo.estado}")
        print(f"   Tipo: {torneo.tipo}")
        print(f"   Lugar: {torneo.lugar}")
        print(f"   Fecha inicio: {torneo.fecha_inicio}")
        
        if torneo.estado == 'oculto':
            print(f"\n✅ El torneo está OCULTO correctamente")
        else:
            print(f"\n⚠️  El torneo está VISIBLE (estado: {torneo.estado})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_estado()
