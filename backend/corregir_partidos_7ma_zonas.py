"""
Script para corregir los partidos de 7ma: asignar zona_id correcta
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Partido
from src.models.torneo_models import TorneoPareja, TorneoCancha, TorneoZona, TorneoZonaPareja

load_dotenv()

def corregir_zonas():
    """Corrige la zona_id de los partidos de 7ma"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔧 CORREGIR ZONA_ID DE PARTIDOS 7MA")
        print("="*80 + "\n")
        
        # Mapeo de parejas a zonas
        # Zona A (158): 494, 462, 479
        # Zona B (159): 467, 465, 466
        # Zona C (160): 463, 493, 461
        # Zona D (161): 464, 492
        
        pareja_a_zona = {
            494: 158, 462: 158, 479: 158,  # Zona A
            467: 159, 465: 159, 466: 159,  # Zona B
            463: 160, 493: 160, 461: 160,  # Zona C
            464: 161, 492: 161              # Zona D
        }
        
        # Obtener todos los partidos de 7ma
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.categoria_id == 85
        ).all()
        
        print(f"Total partidos de 7ma: {len(partidos)}\n")
        
        for partido in partidos:
            # Determinar la zona según las parejas
            pareja1_zona = pareja_a_zona.get(partido.pareja1_id)
            pareja2_zona = pareja_a_zona.get(partido.pareja2_id)
            
            if pareja1_zona and pareja1_zona == pareja2_zona:
                partido.zona_id = pareja1_zona
                zona = db.query(TorneoZona).filter(TorneoZona.id == pareja1_zona).first()
                zona_nombre = zona.nombre if zona else f"Zona {pareja1_zona}"
                
                # Convertir a hora Argentina para mostrar
                fecha_arg = partido.fecha_hora.astimezone()
                fecha_str = fecha_arg.strftime("%Y-%m-%d %H:%M")
                
                print(f"✅ Partido {partido.id_partido}: Pareja {partido.pareja1_id} vs {partido.pareja2_id}")
                print(f"   {zona_nombre} - {fecha_str}")
            else:
                print(f"⚠️  Partido {partido.id_partido}: Parejas de zonas diferentes o no encontradas")
        
        db.commit()
        
        print("\n" + "="*80)
        print("✅ ZONAS CORREGIDAS")
        print("="*80 + "\n")
        
        # Verificar por zona
        print("🔍 Partidos por zona:")
        print("-" * 80)
        
        for zona_id in [158, 159, 160, 161]:
            zona = db.query(TorneoZona).filter(TorneoZona.id == zona_id).first()
            if not zona:
                continue
            
            print(f"\n📋 {zona.nombre} (ID: {zona_id})")
            print("-" * 80)
            
            partidos_zona = db.query(Partido).filter(
                Partido.id_torneo == 37,
                Partido.categoria_id == 85,
                Partido.zona_id == zona_id
            ).order_by(Partido.fecha_hora).all()
            
            for partido in partidos_zona:
                cancha = db.query(TorneoCancha).filter(TorneoCancha.id == partido.cancha_id).first()
                cancha_nombre = cancha.nombre if cancha else "Sin cancha"
                
                # Convertir a hora Argentina
                fecha_arg = partido.fecha_hora.astimezone()
                fecha_str = fecha_arg.strftime("%d/%m %H:%M")
                
                print(f"  {fecha_str} | {cancha_nombre} | Pareja {partido.pareja1_id} vs {partido.pareja2_id}")
            
            if not partidos_zona:
                print("  (Sin partidos)")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    corregir_zonas()
