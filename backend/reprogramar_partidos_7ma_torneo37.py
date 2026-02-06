"""
Script para reprogramar los partidos de 7ma según el organizador
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Partido
from src.models.torneo_models import TorneoPareja, TorneoCancha
from datetime import datetime
import pytz

load_dotenv()

def reprogramar_partidos():
    """Reprograma los partidos de 7ma según el organizador"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔄 REPROGRAMAR PARTIDOS 7MA - TORNEO 37")
        print("="*80 + "\n")
        
        # UTC (guardar hora Argentina directamente como UTC)
        utc = pytz.UTC
        
        # Obtener canchas
        cancha1 = db.query(TorneoCancha).filter(
            TorneoCancha.torneo_id == 37,
            TorneoCancha.nombre == "Cancha 1"
        ).first()
        
        cancha2 = db.query(TorneoCancha).filter(
            TorneoCancha.torneo_id == 37,
            TorneoCancha.nombre == "Cancha 2"
        ).first()
        
        if not cancha1 or not cancha2:
            print("❌ No se encontraron las canchas")
            return
        
        print(f"Cancha 1 ID: {cancha1.id}")
        print(f"Cancha 2 ID: {cancha2.id}\n")
        
        # Eliminar partidos actuales de 7ma
        print("🗑️  Eliminando partidos actuales de 7ma...")
        partidos_eliminados = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.categoria_id == 85  # 7ma
        ).delete(synchronize_session=False)
        
        print(f"✅ {partidos_eliminados} partidos eliminados\n")
        
        # Programación según el organizador:
        # Zona A: Ruarte (494) vs Romero (462) hoy 17hs, Ruarte vs Coppede (479) hoy 19hs, Romero vs Coppede hoy 22hs
        # Zona B: Giordano (467) vs Sanchez (466) hoy 16hs, Giordano vs Barrera (465) hoy 00hs, Barrera vs Sanchez (pendiente)
        # Zona C: Bicet (463) vs Montivero (461) sábado 15hs, Bicet vs Campos (493) sábado 19hs, Campos vs Montivero sábado 22hs
        # Zona D: Leterrucci (464) vs Folledo (492) hoy 20hs
        
        partidos_programar = [
            # Zona A - Viernes
            {"pareja1": 494, "pareja2": 462, "fecha": "2026-02-06 17:00:00", "cancha": cancha1.id},  # Ruarte vs Romero
            {"pareja1": 494, "pareja2": 479, "fecha": "2026-02-06 19:00:00", "cancha": cancha1.id},  # Ruarte vs Coppede
            {"pareja1": 462, "pareja2": 479, "fecha": "2026-02-06 22:00:00", "cancha": cancha1.id},  # Romero vs Coppede
            
            # Zona B - Viernes
            {"pareja1": 467, "pareja2": 466, "fecha": "2026-02-06 16:00:00", "cancha": cancha2.id},  # Giordano vs Sanchez
            {"pareja1": 467, "pareja2": 465, "fecha": "2026-02-07 00:00:00", "cancha": cancha2.id},  # Giordano vs Barrera (medianoche = sábado 00:00)
            
            # Zona C - Sábado
            {"pareja1": 463, "pareja2": 461, "fecha": "2026-02-07 15:00:00", "cancha": cancha1.id},  # Bicet vs Montivero
            {"pareja1": 463, "pareja2": 493, "fecha": "2026-02-07 19:00:00", "cancha": cancha1.id},  # Bicet vs Campos
            {"pareja1": 493, "pareja2": 461, "fecha": "2026-02-07 22:00:00", "cancha": cancha1.id},  # Campos vs Montivero
            
            # Zona D - Viernes
            {"pareja1": 464, "pareja2": 492, "fecha": "2026-02-06 20:00:00", "cancha": cancha2.id},  # Leterrucci vs Folledo
        ]
        
        print("📅 Programando partidos:")
        print("-" * 80)
        
        for idx, partido_data in enumerate(partidos_programar, 1):
            pareja1 = db.query(TorneoPareja).filter(TorneoPareja.id == partido_data["pareja1"]).first()
            pareja2 = db.query(TorneoPareja).filter(TorneoPareja.id == partido_data["pareja2"]).first()
            
            if not pareja1 or not pareja2:
                print(f"❌ Partido {idx}: Parejas no encontradas")
                continue
            
            # Crear fecha como UTC directamente (sin conversión)
            fecha_naive = datetime.strptime(partido_data["fecha"], "%Y-%m-%d %H:%M:%S")
            fecha_tz = utc.localize(fecha_naive)
            
            # Crear partido
            nuevo_partido = Partido(
                id_torneo=37,
                categoria_id=85,  # 7ma
                tipo="torneo",
                fase="zona",
                pareja1_id=pareja1.id,
                pareja2_id=pareja2.id,
                cancha_id=partido_data["cancha"],
                fecha_hora=fecha_tz,
                fecha=fecha_tz,
                estado="pendiente",
                creado_por=2,  # Tu usuario
                id_creador=2
            )
            
            db.add(nuevo_partido)
            
            cancha_nombre = "Cancha 1" if partido_data["cancha"] == cancha1.id else "Cancha 2"
            print(f"  ✅ Partido {idx}: Pareja {pareja1.id} vs {pareja2.id} - {partido_data['fecha']} - {cancha_nombre}")
        
        db.commit()
        
        print("\n" + "="*80)
        print("✅ PARTIDOS REPROGRAMADOS")
        print("="*80 + "\n")
        
        # Verificar
        print("🔍 Verificación:")
        print("-" * 80)
        partidos_7ma = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.categoria_id == 85
        ).order_by(Partido.fecha_hora).all()
        
        print(f"Total partidos 7ma programados: {len(partidos_7ma)}\n")
        
        for partido in partidos_7ma:
            cancha = db.query(TorneoCancha).filter(TorneoCancha.id == partido.cancha_id).first()
            cancha_nombre = cancha.nombre if cancha else "Sin cancha"
            fecha_str = partido.fecha_hora.strftime("%Y-%m-%d %H:%M")
            print(f"  Partido {partido.id_partido}: Pareja {partido.pareja1_id} vs {partido.pareja2_id} - {fecha_str} - {cancha_nombre}")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reprogramar_partidos()
