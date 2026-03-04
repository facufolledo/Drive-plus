"""
Script para mostrar/restaurar el torneo 42 después del pago
Cambia el estado de 'oculto' a 'inscripcion' para que vuelva a aparecer
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

def mostrar_torneo_42(nuevo_estado='inscripcion'):
    """
    Muestra el torneo 42 cambiando su estado
    
    Args:
        nuevo_estado: Estado al que cambiar ('inscripcion', 'programado', 'fase_grupos', etc.)
    """
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
        
        if torneo.estado != 'oculto':
            print(f"\n⚠️  El torneo ya está visible (estado: {torneo.estado})")
            respuesta = input("¿Quieres cambiar el estado de todas formas? (s/n): ")
            if respuesta.lower() != 's':
                print("Operación cancelada")
                return
        
        # Guardar estado anterior
        estado_anterior = torneo.estado
        
        # Cambiar al nuevo estado
        torneo.estado = nuevo_estado
        
        db.commit()
        
        print(f"\n✅ Torneo mostrado exitosamente")
        print(f"   Estado anterior: {estado_anterior}")
        print(f"   Estado nuevo: {torneo.estado}")
        print(f"\n🎉 El torneo ahora aparecerá en los listados públicos")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    # Permitir pasar el estado como argumento
    nuevo_estado = 'inscripcion'
    if len(sys.argv) > 1:
        nuevo_estado = sys.argv[1]
    
    print(f"📋 Cambiando torneo 42 a estado: {nuevo_estado}")
    print("Estados válidos: inscripcion, programado, armando_zonas, fase_grupos, fase_eliminacion, finalizado")
    print()
    
    mostrar_torneo_42(nuevo_estado)
