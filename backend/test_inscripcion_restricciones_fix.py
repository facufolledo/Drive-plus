"""
Test para verificar que las restricciones horarias se guardan correctamente
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.database.config import get_db
from src.models.torneo_models import TorneoPareja
from sqlalchemy import desc

def verificar_ultima_pareja():
    """Verifica la última pareja inscrita y sus restricciones"""
    db = next(get_db())
    
    try:
        # Obtener la última pareja del torneo 37
        pareja = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == 37
        ).order_by(desc(TorneoPareja.id)).first()
        
        if not pareja:
            print("❌ No se encontró ninguna pareja en el torneo 37")
            return
        
        print("\n" + "="*80)
        print("🔍 VERIFICACIÓN DE RESTRICCIONES HORARIAS")
        print("="*80)
        print(f"Pareja ID: {pareja.id}")
        print(f"Jugador 1 ID: {pareja.jugador1_id}")
        print(f"Jugador 2 ID: {pareja.jugador2_id}")
        print(f"Estado: {pareja.estado}")
        print(f"Categoría ID: {pareja.categoria_id}")
        print(f"\n📅 Disponibilidad horaria:")
        print(f"   Tipo: {type(pareja.disponibilidad_horaria)}")
        print(f"   Valor: {pareja.disponibilidad_horaria}")
        
        if pareja.disponibilidad_horaria:
            print(f"\n✅ RESTRICCIONES GUARDADAS CORRECTAMENTE")
            print(f"   Cantidad de franjas: {len(pareja.disponibilidad_horaria)}")
            for idx, franja in enumerate(pareja.disponibilidad_horaria, 1):
                print(f"   Franja {idx}:")
                print(f"      Días: {franja.get('dias', [])}")
                print(f"      Hora inicio: {franja.get('horaInicio', 'N/A')}")
                print(f"      Hora fin: {franja.get('horaFin', 'N/A')}")
        else:
            print(f"\n⚠️  NO HAY RESTRICCIONES GUARDADAS")
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_ultima_pareja()
