"""
Script para ver las parejas de Principiante
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.torneo_models import TorneoPareja, TorneoCategoria
from src.models.driveplus_models import PerfilUsuario

load_dotenv()

def ver_parejas():
    """Ver parejas de Principiante"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("📋 PAREJAS PRINCIPIANTE - TORNEO 37")
        print("="*80 + "\n")
        
        # Obtener categoría Principiante
        categoria = db.query(TorneoCategoria).filter(
            TorneoCategoria.torneo_id == 37,
            TorneoCategoria.nombre == "Principiante"
        ).first()
        
        if not categoria:
            print("❌ Categoría Principiante no encontrada")
            return
        
        # Obtener parejas
        parejas = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == 37,
            TorneoPareja.categoria_id == categoria.id
        ).order_by(TorneoPareja.id).all()
        
        print(f"Total parejas: {len(parejas)}\n")
        
        for pareja in parejas:
            perfil1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
            perfil2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
            
            nombre1 = f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Usuario {pareja.jugador1_id}"
            nombre2 = f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Usuario {pareja.jugador2_id}"
            
            print(f"Pareja {pareja.id}: {nombre1} / {nombre2}")
            print(f"  Estado: {pareja.estado}")
            print()
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    ver_parejas()
