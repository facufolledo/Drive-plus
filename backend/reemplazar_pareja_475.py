"""
Script para reemplazar pareja 475 por Carlos Fernandez / Leo Mena
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.torneo_models import TorneoPareja
from src.models.driveplus_models import Usuario, PerfilUsuario

load_dotenv()

def reemplazar_pareja():
    """Reemplaza la pareja 475"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔄 REEMPLAZAR PAREJA 475")
        print("="*80 + "\n")
        
        # Buscar Carlos Fernandez
        carlos = db.query(PerfilUsuario).filter(
            PerfilUsuario.nombre.ilike('%carlos%'),
            PerfilUsuario.apellido.ilike('%fernandez%')
        ).first()
        
        if not carlos:
            print("❌ Carlos Fernandez no encontrado")
            print("Buscando variantes...")
            # Buscar por apellido solo
            carlos = db.query(PerfilUsuario).filter(
                PerfilUsuario.apellido.ilike('%fernandez%')
            ).first()
        
        # Buscar Leo Mena
        leo = db.query(PerfilUsuario).filter(
            PerfilUsuario.nombre.ilike('%leo%'),
            PerfilUsuario.apellido.ilike('%mena%')
        ).first()
        
        if not leo:
            print("❌ Leo Mena no encontrado")
            print("Buscando variantes...")
            # Buscar por apellido solo
            leo = db.query(PerfilUsuario).filter(
                PerfilUsuario.apellido.ilike('%mena%')
            ).first()
        
        if not carlos or not leo:
            print("\n⚠️  No se encontraron los jugadores. Mostrando todos los perfiles:")
            print("-" * 80)
            
            # Buscar Fernandez
            fernandez_list = db.query(PerfilUsuario).filter(
                PerfilUsuario.apellido.ilike('%fernandez%')
            ).all()
            
            print("\nPerfiles con apellido Fernandez:")
            for p in fernandez_list:
                print(f"  ID: {p.id_usuario} - {p.nombre} {p.apellido}")
            
            # Buscar Mena
            mena_list = db.query(PerfilUsuario).filter(
                PerfilUsuario.apellido.ilike('%mena%')
            ).all()
            
            print("\nPerfiles con apellido Mena:")
            for p in mena_list:
                print(f"  ID: {p.id_usuario} - {p.nombre} {p.apellido}")
            
            return
        
        print(f"✅ Carlos Fernandez encontrado: ID {carlos.id_usuario}")
        print(f"✅ Leo Mena encontrado: ID {leo.id_usuario}\n")
        
        # Obtener pareja 475
        pareja_475 = db.query(TorneoPareja).filter(TorneoPareja.id == 475).first()
        
        if not pareja_475:
            print("❌ Pareja 475 no encontrada")
            return
        
        print(f"Pareja 475 actual:")
        print(f"  Jugador 1 ID: {pareja_475.jugador1_id}")
        print(f"  Jugador 2 ID: {pareja_475.jugador2_id}\n")
        
        # Actualizar pareja
        pareja_475.jugador1_id = carlos.id_usuario
        pareja_475.jugador2_id = leo.id_usuario
        
        db.commit()
        
        print("✅ Pareja 475 actualizada:")
        print(f"  Nuevo Jugador 1: {carlos.nombre} {carlos.apellido} (ID: {carlos.id_usuario})")
        print(f"  Nuevo Jugador 2: {leo.nombre} {leo.apellido} (ID: {leo.id_usuario})")
        
        print("\n" + "="*80)
        print("✅ REEMPLAZO COMPLETADO")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reemplazar_pareja()
