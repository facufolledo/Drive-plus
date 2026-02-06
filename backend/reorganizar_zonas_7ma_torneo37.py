"""
Script para reorganizar las zonas de 7ma según el organizador
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.torneo_models import TorneoZona, TorneoZonaPareja, TorneoPareja
from src.models.driveplus_models import PerfilUsuario

load_dotenv()

def reorganizar_zonas():
    """Reorganiza las zonas de 7ma según el organizador"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔄 REORGANIZAR ZONAS 7MA - TORNEO 37")
        print("="*80 + "\n")
        
        # IDs de zonas
        zona_a_id = 158
        zona_b_id = 159
        zona_c_id = 160
        zona_d_id = 161
        
        # Nueva configuración según el organizador:
        # Zona A: Ruarte/Oliva (494), Romero Jr/Romero (462), Coppede/De la Fuente (479)
        # Zona B: Giordano/Tapia (467), Barrera/Granillo (465), Sanchez/Bordon (466)
        # Zona C: Bicet/Cejas (463), Campos/Molina (493), Montivero/Millicay (461)
        # Zona D: Leterrucci/Guerrero (464), Folledo/Saad (492)
        
        nueva_configuracion = {
            zona_a_id: [494, 462, 479],  # Ruarte, Romero, Coppede
            zona_b_id: [467, 465, 466],  # Giordano, Barrera, Sanchez
            zona_c_id: [463, 493, 461],  # Bicet, Campos, Montivero
            zona_d_id: [464, 492]        # Leterrucci, Folledo
        }
        
        print("📋 Nueva configuración de zonas:")
        print("-" * 80)
        
        for zona_id, parejas_ids in nueva_configuracion.items():
            zona = db.query(TorneoZona).filter(TorneoZona.id == zona_id).first()
            print(f"\n{zona.nombre}:")
            
            for pareja_id in parejas_ids:
                pareja = db.query(TorneoPareja).filter(TorneoPareja.id == pareja_id).first()
                if pareja:
                    p1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
                    p2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
                    nombre = f"{p1.apellido}/{p2.apellido}" if p1 and p2 else f"Pareja {pareja_id}"
                    print(f"  - Pareja {pareja_id}: {nombre}")
        
        print("\n" + "="*80)
        print("🔄 Aplicando cambios...")
        print("="*80 + "\n")
        
        # Eliminar todas las asignaciones actuales de 7ma
        db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.zona_id.in_([zona_a_id, zona_b_id, zona_c_id, zona_d_id])
        ).delete(synchronize_session=False)
        
        # Crear nuevas asignaciones
        for zona_id, parejas_ids in nueva_configuracion.items():
            for pareja_id in parejas_ids:
                nueva_asignacion = TorneoZonaPareja(
                    zona_id=zona_id,
                    pareja_id=pareja_id
                )
                db.add(nueva_asignacion)
        
        db.commit()
        
        print("✅ Zonas reorganizadas correctamente\n")
        
        # Verificar
        print("="*80)
        print("🔍 VERIFICACIÓN")
        print("="*80 + "\n")
        
        for zona_id in [zona_a_id, zona_b_id, zona_c_id, zona_d_id]:
            zona = db.query(TorneoZona).filter(TorneoZona.id == zona_id).first()
            print(f"📋 {zona.nombre}")
            print("-" * 80)
            
            zona_parejas = db.query(TorneoZonaPareja).filter(
                TorneoZonaPareja.zona_id == zona_id
            ).all()
            
            for zp in zona_parejas:
                pareja = db.query(TorneoPareja).filter(TorneoPareja.id == zp.pareja_id).first()
                if pareja:
                    p1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
                    p2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
                    nombre = f"{p1.nombre} {p1.apellido} / {p2.nombre} {p2.apellido}" if p1 and p2 else f"Pareja {pareja.id}"
                    print(f"  Pareja {pareja.id}: {nombre}")
            print()
        
        print("="*80)
        print("✅ REORGANIZACIÓN COMPLETADA")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reorganizar_zonas()
