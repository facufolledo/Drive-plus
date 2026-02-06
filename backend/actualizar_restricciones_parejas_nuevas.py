"""
Script para actualizar restricciones horarias de las parejas nuevas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.torneo_models import TorneoPareja
from src.models.driveplus_models import PerfilUsuario

load_dotenv()

def actualizar_restricciones():
    """Actualiza las restricciones horarias de las 3 parejas nuevas"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔧 ACTUALIZAR RESTRICCIONES HORARIAS - PAREJAS NUEVAS")
        print("="*80 + "\n")
        
        # ============================================
        # PAREJA 493 - Molina / Campos
        # ============================================
        print("📋 PAREJA 493 - Molina / Campos")
        print("-" * 80)
        print("Restricciones (cuando NO pueden jugar):")
        print("  ❌ Viernes: 09:00 - 23:30")
        print("  ❌ Sábado: 09:00 - 15:00")
        
        restricciones_493 = [
            {
                "dias": ["viernes"],
                "horaInicio": "09:00",
                "horaFin": "23:30"
            },
            {
                "dias": ["sabado"],
                "horaInicio": "09:00",
                "horaFin": "15:00"
            }
        ]
        
        pareja_493 = db.query(TorneoPareja).filter(TorneoPareja.id == 493).first()
        if pareja_493:
            pareja_493.disponibilidad_horaria = restricciones_493
            print("✅ Actualizada\n")
        else:
            print("❌ No encontrada\n")
        
        # ============================================
        # PAREJA 494 - Ruarte / Oliva
        # ============================================
        print("📋 PAREJA 494 - Ruarte / Oliva")
        print("-" * 80)
        print("Restricciones (cuando NO pueden jugar):")
        print("  ❌ Viernes: 09:00 - 23:30")
        print("  ❌ Sábado: 09:00 - 16:00")
        
        restricciones_494 = [
            {
                "dias": ["viernes"],
                "horaInicio": "09:00",
                "horaFin": "23:30"
            },
            {
                "dias": ["sabado"],
                "horaInicio": "09:00",
                "horaFin": "16:00"
            }
        ]
        
        pareja_494 = db.query(TorneoPareja).filter(TorneoPareja.id == 494).first()
        if pareja_494:
            pareja_494.disponibilidad_horaria = restricciones_494
            print("✅ Actualizada\n")
        else:
            print("❌ No encontrada\n")
        
        # ============================================
        # PAREJA 495 - Vera / Calderón
        # ============================================
        print("📋 PAREJA 495 - Vera / Calderón")
        print("-" * 80)
        print("Restricciones (cuando NO pueden jugar):")
        print("  ❌ Viernes: 09:00 - 23:30")
        print("  ❌ Sábado: 09:00 - 10:00")
        
        restricciones_495 = [
            {
                "dias": ["viernes"],
                "horaInicio": "09:00",
                "horaFin": "23:30"
            },
            {
                "dias": ["sabado"],
                "horaInicio": "09:00",
                "horaFin": "10:00"
            }
        ]
        
        pareja_495 = db.query(TorneoPareja).filter(TorneoPareja.id == 495).first()
        if pareja_495:
            pareja_495.disponibilidad_horaria = restricciones_495
            print("✅ Actualizada\n")
        else:
            print("❌ No encontrada\n")
        
        db.commit()
        
        # Verificar las actualizaciones
        print("="*80)
        print("🔍 VERIFICACIÓN")
        print("="*80 + "\n")
        
        for pareja_id in [493, 494, 495]:
            pareja = db.query(TorneoPareja).filter(TorneoPareja.id == pareja_id).first()
            
            if pareja:
                perfil1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
                perfil2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
                
                nombre1 = f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Usuario {pareja.jugador1_id}"
                nombre2 = f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Usuario {pareja.jugador2_id}"
                
                print(f"Pareja {pareja.id}: {nombre1} / {nombre2}")
                disponibilidad = pareja.disponibilidad_horaria
                if disponibilidad:
                    print(f"  Disponibilidad guardada:")
                    for idx, franja in enumerate(disponibilidad, 1):
                        print(f"    {idx}. {franja['dias']}: {franja['horaInicio']} - {franja['horaFin']}")
                else:
                    print(f"  ⚠️  Sin restricciones")
                print()
        
        print("="*80)
        print("✅ ACTUALIZACIÓN COMPLETADA")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    actualizar_restricciones()
