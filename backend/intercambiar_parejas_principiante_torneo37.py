"""
Intercambiar parejas entre zonas en Principiante - Torneo 37
- Pareja de Santiago Mazza (Zona A) → Zona de Último Momento
- Pareja de Matias Moreno (Zona Último Momento) → Zona A
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Usuario, Partido
from src.models.torneo_models import TorneoPareja, TorneoZona, TorneoZonaPareja

load_dotenv()

def intercambiar_parejas():
    """Intercambia las parejas entre zonas"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔄 INTERCAMBIO DE PAREJAS - PRINCIPIANTE TORNEO 37")
        print("="*80 + "\n")
        
        # 1. Buscar pareja de Santiago Mazza
        santiago = db.query(Usuario).filter(Usuario.nombre_usuario.ilike('%santiago%mazza%')).first()
        if not santiago:
            santiago = db.query(Usuario).filter(Usuario.nombre_usuario.ilike('%mazza%')).first()
        
        if not santiago:
            print("❌ No se encontró a Santiago Mazza")
            return
        
        print(f"✅ Encontrado: {santiago.nombre_usuario} (ID: {santiago.id_usuario})")
        
        # Buscar su pareja en el torneo 37
        pareja_santiago = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == 37,
            ((TorneoPareja.jugador1_id == santiago.id_usuario) | (TorneoPareja.jugador2_id == santiago.id_usuario))
        ).first()
        
        if not pareja_santiago:
            print("❌ No se encontró la pareja de Santiago en el torneo 37")
            return
        
        # Obtener compañero
        companero_santiago_id = pareja_santiago.jugador2_id if pareja_santiago.jugador1_id == santiago.id_usuario else pareja_santiago.jugador1_id
        companero_santiago = db.query(Usuario).filter(Usuario.id_usuario == companero_santiago_id).first()
        
        print(f"   Pareja ID: {pareja_santiago.id}")
        print(f"   Compañero: {companero_santiago.nombre_usuario if companero_santiago else 'N/A'}")
        
        # 2. Buscar pareja de Matias Moreno
        matias = db.query(Usuario).filter(Usuario.nombre_usuario.ilike('%matias%moreno%')).first()
        if not matias:
            matias = db.query(Usuario).filter(Usuario.nombre_usuario.ilike('%moreno%')).first()
        
        if not matias:
            print("\n❌ No se encontró a Matias Moreno")
            return
        
        print(f"\n✅ Encontrado: {matias.nombre_usuario} (ID: {matias.id_usuario})")
        
        # Buscar su pareja en el torneo 37
        pareja_matias = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == 37,
            ((TorneoPareja.jugador1_id == matias.id_usuario) | (TorneoPareja.jugador2_id == matias.id_usuario))
        ).first()
        
        if not pareja_matias:
            print("❌ No se encontró la pareja de Matias en el torneo 37")
            return
        
        # Obtener compañero
        companero_matias_id = pareja_matias.jugador2_id if pareja_matias.jugador1_id == matias.id_usuario else pareja_matias.jugador1_id
        companero_matias = db.query(Usuario).filter(Usuario.id_usuario == companero_matias_id).first()
        
        print(f"   Pareja ID: {pareja_matias.id}")
        print(f"   Compañero: {companero_matias.nombre_usuario if companero_matias else 'N/A'}")
        
        # 3. Obtener zonas actuales
        zona_santiago = db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.pareja_id == pareja_santiago.id
        ).first()
        
        zona_matias = db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.pareja_id == pareja_matias.id
        ).first()
        
        if not zona_santiago or not zona_matias:
            print("\n❌ No se encontraron las zonas de las parejas")
            return
        
        # Obtener nombres de zonas
        zona_santiago_obj = db.query(TorneoZona).filter(TorneoZona.id == zona_santiago.zona_id).first()
        zona_matias_obj = db.query(TorneoZona).filter(TorneoZona.id == zona_matias.zona_id).first()
        
        print(f"\n📍 Zona actual de Santiago: {zona_santiago_obj.nombre if zona_santiago_obj else 'N/A'} (ID: {zona_santiago.zona_id})")
        print(f"📍 Zona actual de Matias: {zona_matias_obj.nombre if zona_matias_obj else 'N/A'} (ID: {zona_matias.zona_id})")
        
        # 4. Intercambiar zonas
        print("\n🔄 Intercambiando zonas...")
        
        zona_temp = zona_santiago.zona_id
        zona_santiago.zona_id = zona_matias.zona_id
        zona_matias.zona_id = zona_temp
        
        db.commit()
        
        print(f"✅ Santiago Mazza → {zona_matias_obj.nombre if zona_matias_obj else 'N/A'}")
        print(f"✅ Matias Moreno → {zona_santiago_obj.nombre if zona_santiago_obj else 'N/A'}")
        
        # 5. Actualizar partidos si es necesario
        print("\n🔄 Actualizando partidos...")
        
        # Partidos de Santiago
        partidos_santiago = db.query(Partido).filter(
            Partido.id_torneo == 37,
            ((Partido.pareja1_id == pareja_santiago.id) | (Partido.pareja2_id == pareja_santiago.id))
        ).all()
        
        for partido in partidos_santiago:
            if partido.zona_id != zona_santiago.zona_id:
                print(f"   Actualizando partido {partido.id_partido}: zona {partido.zona_id} → {zona_santiago.zona_id}")
                partido.zona_id = zona_santiago.zona_id
        
        # Partidos de Matias
        partidos_matias = db.query(Partido).filter(
            Partido.id_torneo == 37,
            ((Partido.pareja1_id == pareja_matias.id) | (Partido.pareja2_id == pareja_matias.id))
        ).all()
        
        for partido in partidos_matias:
            if partido.zona_id != zona_matias.zona_id:
                print(f"   Actualizando partido {partido.id_partido}: zona {partido.zona_id} → {zona_matias.zona_id}")
                partido.zona_id = zona_matias.zona_id
        
        db.commit()
        
        print("\n" + "="*80)
        print("✅ INTERCAMBIO COMPLETADO")
        print("="*80)
        print(f"\nParejas intercambiadas:")
        print(f"  • Santiago Mazza / {companero_santiago.nombre_usuario if companero_santiago else 'N/A'}")
        print(f"    Zona: {zona_santiago_obj.nombre if zona_santiago_obj else 'N/A'} → {zona_matias_obj.nombre if zona_matias_obj else 'N/A'}")
        print(f"\n  • Matias Moreno / {companero_matias.nombre_usuario if companero_matias else 'N/A'}")
        print(f"    Zona: {zona_matias_obj.nombre if zona_matias_obj else 'N/A'} → {zona_santiago_obj.nombre if zona_santiago_obj else 'N/A'}")
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    intercambiar_parejas()
