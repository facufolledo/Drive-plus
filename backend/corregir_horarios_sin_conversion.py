"""
Script para corregir los horarios de 7ma
Guardar la hora Argentina directamente como UTC (sin conversión)
porque el frontend hace la conversión automática
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Partido
from datetime import datetime
import pytz

load_dotenv()

def corregir_horarios():
    """Corrige los horarios guardando la hora Argentina como UTC"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔧 CORREGIR HORARIOS - GUARDAR HORA ARG COMO UTC")
        print("="*80 + "\n")
        
        # Horarios que quiero que se MUESTREN en el frontend (hora Argentina)
        horarios_mostrar = {
            # Zona A
            181: ("2026-02-06 17:00:00", "Ruarte vs Romero"),
            182: ("2026-02-06 19:00:00", "Ruarte vs Coppede"),
            183: ("2026-02-06 22:00:00", "Romero vs Coppede"),
            
            # Zona B
            184: ("2026-02-06 16:00:00", "Giordano vs Sanchez"),
            185: ("2026-02-07 00:00:00", "Giordano vs Barrera"),
            190: ("2026-02-07 17:00:00", "Barrera vs Sanchez"),
            
            # Zona C
            186: ("2026-02-07 15:00:00", "Bicet vs Montivero"),
            187: ("2026-02-07 19:00:00", "Bicet vs Campos"),
            188: ("2026-02-07 22:00:00", "Campos vs Montivero"),
            
            # Zona D
            189: ("2026-02-06 20:00:00", "Leterrucci vs Folledo"),
        }
        
        print("Guardando horarios (hora a mostrar = hora a guardar en UTC)...")
        print("-" * 80)
        
        utc = pytz.UTC
        
        for partido_id, (fecha_str, descripcion) in horarios_mostrar.items():
            partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
            
            if not partido:
                print(f"⚠️  Partido {partido_id} no encontrado")
                continue
            
            # Parsear fecha y marcarla como UTC directamente
            fecha_naive = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            fecha_utc = utc.localize(fecha_naive)
            
            # Actualizar partido
            partido.fecha_hora = fecha_utc
            partido.fecha = fecha_utc
            
            print(f"✅ Partido {partido_id}: {descripcion}")
            print(f"   Guardar en BD: {fecha_utc.strftime('%Y-%m-%d %H:%M UTC')}")
            print(f"   Se mostrará: {fecha_str}")
        
        db.commit()
        
        print("\n" + "="*80)
        print("✅ HORARIOS CORREGIDOS")
        print("="*80 + "\n")
        
        # Verificar
        print("🔍 Verificación (hora guardada en BD como UTC):")
        print("-" * 80)
        
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.categoria_id == 85
        ).order_by(Partido.fecha_hora).all()
        
        for partido in partidos:
            fecha_str = partido.fecha_hora.strftime("%d/%m %H:%M UTC")
            print(f"  Partido {partido.id_partido}: {fecha_str} | Pareja {partido.pareja1_id} vs {partido.pareja2_id}")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    corregir_horarios()
