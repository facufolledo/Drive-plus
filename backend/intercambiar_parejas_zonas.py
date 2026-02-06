"""
Script para intercambiar parejas entre zonas
Pareja 492 (Folledo/Saad) de Zona B a Zona D
Pareja 465 (Barrera/Granillo) de Zona D a Zona B
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

def intercambiar_parejas():
    """Intercambia las parejas 492 y 465 entre Zona B y Zona D"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔄 INTERCAMBIAR PAREJAS ENTRE ZONAS")
        print("="*80 + "\n")
        
        # IDs
        pareja_492_id = 492  # Folledo/Saad
        pareja_465_id = 465  # Barrera/Granillo
        zona_b_id = 159
        zona_d_id = 161
        
        # Obtener información de las parejas
        pareja_492 = db.query(TorneoPareja).filter(TorneoPareja.id == pareja_492_id).first()
        pareja_465 = db.query(TorneoPareja).filter(TorneoPareja.id == pareja_465_id).first()
        
        if not pareja_492 or not pareja_465:
            print("❌ No se encontraron las parejas")
            return
        
        # Obtener perfiles para mostrar nombres
        perfil_492_1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja_492.jugador1_id).first()
        perfil_492_2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja_492.jugador2_id).first()
        perfil_465_1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja_465.jugador1_id).first()
        perfil_465_2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja_465.jugador2_id).first()
        
        nombre_492 = f"{perfil_492_1.nombre} {perfil_492_1.apellido} / {perfil_492_2.nombre} {perfil_492_2.apellido}"
        nombre_465 = f"{perfil_465_1.nombre} {perfil_465_1.apellido} / {perfil_465_2.nombre} {perfil_465_2.apellido}"
        
        print(f"Pareja 492: {nombre_492}")
        print(f"Pareja 465: {nombre_465}\n")
        
        # Buscar las asignaciones actuales
        zona_pareja_492 = db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.pareja_id == pareja_492_id
        ).first()
        
        zona_pareja_465 = db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.pareja_id == pareja_465_id
        ).first()
        
        if not zona_pareja_492 or not zona_pareja_465:
            print("❌ No se encontraron las asignaciones de zona")
            return
        
        print(f"Estado actual:")
        print(f"  Pareja 492 está en Zona ID: {zona_pareja_492.zona_id}")
        print(f"  Pareja 465 está en Zona ID: {zona_pareja_465.zona_id}\n")
        
        # Intercambiar
        print("🔄 Intercambiando...")
        zona_pareja_492.zona_id = zona_d_id  # Folledo/Saad → Zona D
        zona_pareja_465.zona_id = zona_b_id  # Barrera/Granillo → Zona B
        
        db.commit()
        
        print("✅ Intercambio completado\n")
        
        # Verificar
        print("="*80)
        print("🔍 VERIFICACIÓN")
        print("="*80 + "\n")
        
        zona_b = db.query(TorneoZona).filter(TorneoZona.id == zona_b_id).first()
        zona_d = db.query(TorneoZona).filter(TorneoZona.id == zona_d_id).first()
        
        print(f"📋 {zona_b.nombre}")
        print("-" * 80)
        parejas_b = db.query(TorneoZonaPareja).filter(TorneoZonaPareja.zona_id == zona_b_id).all()
        for zp in parejas_b:
            pareja = db.query(TorneoPareja).filter(TorneoPareja.id == zp.pareja_id).first()
            perfil1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
            perfil2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
            nombre = f"{perfil1.nombre} {perfil1.apellido} / {perfil2.nombre} {perfil2.apellido}"
            print(f"  Pareja {pareja.id}: {nombre}")
        
        print(f"\n📋 {zona_d.nombre}")
        print("-" * 80)
        parejas_d = db.query(TorneoZonaPareja).filter(TorneoZonaPareja.zona_id == zona_d_id).all()
        for zp in parejas_d:
            pareja = db.query(TorneoPareja).filter(TorneoPareja.id == zp.pareja_id).first()
            perfil1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
            perfil2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
            nombre = f"{perfil1.nombre} {perfil1.apellido} / {perfil2.nombre} {perfil2.apellido}"
            print(f"  Pareja {pareja.id}: {nombre}")
        
        print("\n" + "="*80)
        print("✅ INTERCAMBIO COMPLETADO")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    intercambiar_parejas()
