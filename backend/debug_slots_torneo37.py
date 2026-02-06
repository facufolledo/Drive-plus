"""
Debug de generación de slots para el torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.services.torneo_fixture_global_service import TorneoFixtureGlobalService
from src.models.torneo_models import Torneo

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def debug_slots():
    session = Session()
    
    try:
        print("=" * 80)
        print("DEBUG: GENERACIÓN DE SLOTS TORNEO 37")
        print("=" * 80)
        
        # Obtener torneo
        torneo = session.query(Torneo).filter(Torneo.id == 37).first()
        
        if not torneo:
            print("\n❌ Torneo 37 no encontrado")
            return
        
        print(f"\n📋 TORNEO: {torneo.nombre}")
        print(f"   Fecha inicio: {torneo.fecha_inicio}")
        print(f"   Fecha fin: {torneo.fecha_fin}")
        print(f"\n⏰ HORARIOS CONFIGURADOS:")
        
        import json
        print(json.dumps(torneo.horarios_disponibles, indent=2))
        
        # Generar slots
        print(f"\n\n{'=' * 80}")
        print("SLOTS GENERADOS:")
        print("=" * 80)
        
        slots = TorneoFixtureGlobalService._generar_slots_torneo(
            torneo, 
            torneo.horarios_disponibles
        )
        
        print(f"\n📊 Total de slots: {len(slots)}")
        
        # Agrupar por día
        slots_por_dia = {}
        for fecha, dia, hora in slots:
            if fecha not in slots_por_dia:
                slots_por_dia[fecha] = []
            slots_por_dia[fecha].append((dia, hora))
        
        for fecha in sorted(slots_por_dia.keys()):
            dia_slots = slots_por_dia[fecha]
            dia_nombre = dia_slots[0][0] if dia_slots else "desconocido"
            
            print(f"\n📅 {fecha} ({dia_nombre}): {len(dia_slots)} slots")
            
            # Mostrar primeros y últimos 3 slots
            if len(dia_slots) <= 6:
                for dia, hora in dia_slots:
                    print(f"   • {hora}")
            else:
                print(f"   Primeros 3:")
                for dia, hora in dia_slots[:3]:
                    print(f"   • {hora}")
                print(f"   ...")
                print(f"   Últimos 3:")
                for dia, hora in dia_slots[-3:]:
                    print(f"   • {hora}")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_slots()
