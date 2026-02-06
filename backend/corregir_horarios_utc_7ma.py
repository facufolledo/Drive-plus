"""
Script para corregir los horarios de 7ma a UTC correcto
Hora Argentina (UTC-3) -> UTC
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Partido
from datetime import datetime, timedelta
import pytz

load_dotenv()

def corregir_horarios():
    """Corrige los horarios de 7ma para que se guarden correctamente en UTC"""
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🔧 CORREGIR HORARIOS UTC - 7MA")
        print("="*80 + "\n")
        
        # Mapeo de partidos con sus horarios CORRECTOS en hora Argentina
        # Formato: partido_id -> (fecha_arg_str, descripcion)
        horarios_correctos = {
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
        
        print("Corrigiendo horarios a UTC...")
        print("-" * 80)
        
        for partido_id, (fecha_arg_str, descripcion) in horarios_correctos.items():
            partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
            
            if not partido:
                print(f"⚠️  Partido {partido_id} no encontrado")
                continue
            
            # Parsear fecha en hora Argentina
            fecha_naive = datetime.strptime(fecha_arg_str, "%Y-%m-%d %H:%M:%S")
            
            # Crear timezone Argentina
            tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
            fecha_arg = tz_arg.localize(fecha_naive)
            
            # Convertir a UTC
            fecha_utc = fecha_arg.astimezone(pytz.UTC)
            
            # Actualizar partido
            partido.fecha_hora = fecha_utc
            partido.fecha = fecha_utc
            
            print(f"✅ Partido {partido_id}: {descripcion}")
            print(f"   ARG: {fecha_arg.strftime('%Y-%m-%d %H:%M %Z')}")
            print(f"   UTC: {fecha_utc.strftime('%Y-%m-%d %H:%M %Z')}")
        
        db.commit()
        
        print("\n" + "="*80)
        print("✅ HORARIOS CORREGIDOS")
        print("="*80 + "\n")
        
        # Verificar
        print("🔍 Verificación (mostrando en hora Argentina):")
        print("-" * 80)
        
        partidos = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.categoria_id == 85
        ).order_by(Partido.fecha_hora).all()
        
        tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
        
        for partido in partidos:
            # Convertir de UTC a Argentina
            fecha_arg = partido.fecha_hora.astimezone(tz_arg)
            fecha_str = fecha_arg.strftime("%d/%m %H:%M")
            
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
