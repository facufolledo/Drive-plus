"""
Script para verificar las zonas de 7ma en el torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.torneo_models import TorneoZona, TorneoZonaPareja, TorneoPareja, TorneoCategoria
from src.models.driveplus_models import PerfilUsuario

load_dotenv()

def verificar_zonas():
    """Verifica las zonas de 7ma"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 ZONAS DE 7MA - TORNEO 37")
        print("="*80 + "\n")
        
        # Obtener categoría 7ma
        categoria_7ma = db.query(TorneoCategoria).filter(
            TorneoCategoria.torneo_id == 37,
            TorneoCategoria.nombre == "7ma"
        ).first()
        
        if not categoria_7ma:
            print("❌ Categoría 7ma no encontrada")
            return
        
        print(f"Categoría 7ma ID: {categoria_7ma.id}\n")
        
        # Obtener zonas de 7ma
        zonas = db.query(TorneoZona).filter(
            TorneoZona.torneo_id == 37,
            TorneoZona.categoria_id == categoria_7ma.id
        ).order_by(TorneoZona.numero_orden).all()
        
        for zona in zonas:
            print(f"📋 {zona.nombre} (ID: {zona.id})")
            print("-" * 80)
            
            # Obtener parejas de la zona
            zona_parejas = db.query(TorneoZonaPareja).filter(
                TorneoZonaPareja.zona_id == zona.id
            ).all()
            
            for zp in zona_parejas:
                pareja = db.query(TorneoPareja).filter(TorneoPareja.id == zp.pareja_id).first()
                
                if pareja:
                    perfil1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
                    perfil2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
                    
                    nombre1 = f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Usuario {pareja.jugador1_id}"
                    nombre2 = f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Usuario {pareja.jugador2_id}"
                    
                    print(f"  Pareja {pareja.id}: {nombre1} / {nombre2}")
            
            print()
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_zonas()
