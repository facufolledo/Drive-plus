"""
Script para verificar las 3 parejas nuevas inscritas
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

def verificar_parejas():
    """Verifica las 3 parejas nuevas"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔍 VERIFICACIÓN PAREJAS NUEVAS - TORNEO 37")
        print("="*80 + "\n")
        
        for pareja_id in [493, 494, 495]:
            pareja = db.query(TorneoPareja).filter(TorneoPareja.id == pareja_id).first()
            
            if not pareja:
                print(f"❌ Pareja {pareja_id} no encontrada\n")
                continue
            
            # Obtener perfiles
            perfil1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
            perfil2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
            
            nombre1 = f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Usuario {pareja.jugador1_id}"
            nombre2 = f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Usuario {pareja.jugador2_id}"
            
            # Obtener categoría
            categoria = db.query(TorneoCategoria).filter(TorneoCategoria.id == pareja.categoria_id).first()
            categoria_nombre = categoria.nombre if categoria else "Sin categoría"
            
            print(f"📋 PAREJA {pareja.id}")
            print("-" * 80)
            print(f"  Jugadores: {nombre1} / {nombre2}")
            print(f"  Categoría: {categoria_nombre}")
            print(f"  Estado: {pareja.estado}")
            print(f"  Torneo ID: {pareja.torneo_id}")
            
            # Mostrar disponibilidad horaria
            disponibilidad = pareja.disponibilidad_horaria
            if disponibilidad:
                print(f"  Disponibilidad horaria:")
                for idx, franja in enumerate(disponibilidad, 1):
                    dias = ", ".join(franja['dias'])
                    print(f"    {idx}. {dias}: {franja['horaInicio']} - {franja['horaFin']}")
            else:
                print(f"  ⚠️  Sin restricciones horarias")
            
            print()
        
        print("="*80)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_parejas()
