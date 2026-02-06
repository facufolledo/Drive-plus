"""
Script para agregar el partido Barrera vs Sanchez
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

def agregar_partido():
    """Agrega el partido Barrera vs Sanchez"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("➕ AGREGAR PARTIDO BARRERA VS SANCHEZ")
        print("="*80 + "\n")
        
        # Obtener parejas
        pareja_barrera = db.query(TorneoPareja).filter(TorneoPareja.id == 465).first()  # Barrera/Granillo
        pareja_sanchez = db.query(TorneoPareja).filter(TorneoPareja.id == 466).first()  # Sanchez/Bordon
        
        if not pareja_barrera or not pareja_sanchez:
            print("❌ Parejas no encontradas")
            return
        
        print("Pareja Barrera/Granillo (465):")
        print(f"  Restricciones: {pareja_barrera.disponibilidad_horaria}")
        
        print("\nPareja Sanchez/Bordon (466):")
        print(f"  Restricciones: {pareja_sanchez.disponibilidad_horaria}")
        
        # Ambas parejas no tienen restricciones, pueden jugar cualquier día
        # Voy a programarlo el sábado a las 17:00 (entre los otros partidos de la zona B)
        
        # Timezone
        tz = pytz.timezone('America/Argentina/Buenos_Aires')
        
        # Obtener cancha 2
        cancha2 = db.query(TorneoCancha).filter(
            TorneoCancha.torneo_id == 37,
            TorneoCancha.nombre == "Cancha 2"
        ).first()
        
        if not cancha2:
            print("❌ Cancha 2 no encontrada")
            return
        
        # Crear fecha: Sábado 7 de febrero 2026 a las 17:00
        fecha_naive = datetime.strptime("2026-02-07 17:00:00", "%Y-%m-%d %H:%M:%S")
        fecha_tz = tz.localize(fecha_naive)
        
        # Crear partido
        nuevo_partido = Partido(
            id_torneo=37,
            categoria_id=85,  # 7ma
            tipo="torneo",
            fase="zona",
            pareja1_id=465,  # Barrera/Granillo
            pareja2_id=466,  # Sanchez/Bordon
            cancha_id=cancha2.id,
            fecha_hora=fecha_tz,
            fecha=fecha_tz,
            estado="pendiente",
            creado_por=2,
            id_creador=2
        )
        
        db.add(nuevo_partido)
        db.commit()
        
        print(f"\n✅ Partido agregado:")
        print(f"   Barrera/Granillo vs Sanchez/Bordon")
        print(f"   Sábado 7/2/2026 - 17:00")
        print(f"   Cancha 2")
        print(f"   ID: {nuevo_partido.id_partido}")
        
        print("\n" + "="*80)
        print("✅ PARTIDO AGREGADO")
        print("="*80 + "\n")
        
        # Verificar todos los partidos de 7ma
        print("🔍 Todos los partidos de 7ma:")
        print("-" * 80)
        
        partidos_7ma = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.categoria_id == 85
        ).order_by(Partido.fecha_hora).all()
        
        for partido in partidos_7ma:
            cancha = db.query(TorneoCancha).filter(TorneoCancha.id == partido.cancha_id).first()
            cancha_nombre = cancha.nombre if cancha else "Sin cancha"
            fecha_str = partido.fecha_hora.strftime("%Y-%m-%d %H:%M")
            print(f"  Partido {partido.id_partido}: Pareja {partido.pareja1_id} vs {partido.pareja2_id} - {fecha_str} - {cancha_nombre}")
        
        print(f"\nTotal: {len(partidos_7ma)} partidos")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    agregar_partido()
