"""
Script para finalizar el fixture de 7ma: agregar partido faltante y asignar zonas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Partido
from src.models.torneo_models import TorneoCancha
from datetime import datetime
import pytz

load_dotenv()

def finalizar_fixture():
    """Agrega el partido faltante y asigna zonas"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔧 FINALIZAR FIXTURE 7MA")
        print("="*80 + "\n")
        
        # Agregar partido Barrera vs Sanchez
        print("➕ Agregando partido Barrera vs Sanchez...")
        
        cancha2 = db.query(TorneoCancha).filter(
            TorneoCancha.torneo_id == 37,
            TorneoCancha.nombre == "Cancha 2"
        ).first()
        
        utc = pytz.UTC
        fecha_naive = datetime.strptime("2026-02-07 17:00:00", "%Y-%m-%d %H:%M:%S")
        fecha_utc = utc.localize(fecha_naive)
        
        nuevo_partido = Partido(
            id_torneo=37,
            categoria_id=85,
            tipo="torneo",
            fase="zona",
            pareja1_id=465,  # Barrera/Granillo
            pareja2_id=466,  # Sanchez/Bordon
            cancha_id=cancha2.id,
            fecha_hora=fecha_utc,
            fecha=fecha_utc,
            estado="pendiente",
            creado_por=2,
            id_creador=2,
            zona_id=159  # Zona B
        )
        
        db.add(nuevo_partido)
        db.flush()
        
        print(f"✅ Partido agregado: ID {nuevo_partido.id_partido}\n")
        
        # Asignar zonas a todos los partidos
        print("🔧 Asignando zonas...")
        
        pareja_a_zona = {
            494: 158, 462: 158, 479: 158,  # Zona A
            467: 159, 465: 159, 466: 159,  # Zona B
            463: 160, 493: 160, 461: 160,  # Zona C
            464: 161, 492: 161              # Zona D
        }
        
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.categoria_id == 85
        ).all()
        
        for partido in partidos:
            pareja1_zona = pareja_a_zona.get(partido.pareja1_id)
            pareja2_zona = pareja_a_zona.get(partido.pareja2_id)
            
            if pareja1_zona and pareja1_zona == pareja2_zona:
                partido.zona_id = pareja1_zona
        
        db.commit()
        
        print("✅ Zonas asignadas\n")
        
        # Verificar
        print("="*80)
        print("🔍 VERIFICACIÓN FINAL")
        print("="*80 + "\n")
        
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.categoria_id == 85
        ).order_by(Partido.fecha_hora).all()
        
        print(f"Total partidos: {len(partidos)}\n")
        
        for zona_id in [158, 159, 160, 161]:
            partidos_zona = [p for p in partidos if p.zona_id == zona_id]
            zona_nombre = {158: "Zona A", 159: "Zona B", 160: "Zona C", 161: "Zona D"}[zona_id]
            
            print(f"📋 {zona_nombre}")
            print("-" * 80)
            
            for p in partidos_zona:
                fecha_str = p.fecha_hora.strftime("%d/%m %H:%M")
                cancha = db.query(TorneoCancha).filter(TorneoCancha.id == p.cancha_id).first()
                cancha_nombre = cancha.nombre if cancha else "?"
                print(f"  {fecha_str} | {cancha_nombre} | Pareja {p.pareja1_id} vs {p.pareja2_id}")
            
            print()
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    finalizar_fixture()
