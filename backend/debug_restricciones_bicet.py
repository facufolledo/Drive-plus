"""
Debug de restricciones de Diego Bicet / Juan Cejas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def debug_restricciones():
    session = Session()
    
    try:
        print("=" * 80)
        print("DEBUG: RESTRICCIONES DIEGO BICET / JUAN CEJAS")
        print("=" * 80)
        
        # Obtener pareja 463
        pareja = session.execute(
            text("""
                SELECT 
                    id,
                    disponibilidad_horaria,
                    jugador1_id,
                    jugador2_id
                FROM torneos_parejas
                WHERE id = 463
            """)
        ).fetchone()
        
        if not pareja:
            print("❌ Pareja 463 no encontrada")
            return
        
        print(f"\n📋 PAREJA #{pareja[0]}")
        print(f"   Jugador 1 ID: {pareja[2]}")
        print(f"   Jugador 2 ID: {pareja[3]}")
        
        restricciones = pareja[1]
        print(f"\n🔍 RESTRICCIONES RAW:")
        print(f"   Tipo: {type(restricciones)}")
        print(f"   Valor: {restricciones}")
        
        if restricciones:
            print(f"\n📊 RESTRICCIONES PROCESADAS:")
            for i, r in enumerate(restricciones):
                print(f"\n   Restricción {i+1}:")
                print(f"      Días: {r.get('dias', [])}")
                print(f"      Hora inicio: {r.get('horaInicio', 'N/A')}")
                print(f"      Hora fin: {r.get('horaFin', 'N/A')}")
                
                # Convertir a minutos
                hora_inicio = r.get('horaInicio', '00:00')
                hora_fin = r.get('horaFin', '23:59')
                inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                
                print(f"      Inicio (mins): {inicio_mins}")
                print(f"      Fin (mins): {fin_mins}")
        
        # Simular verificación para viernes 16:10
        print(f"\n🧪 SIMULACIÓN: Viernes 16:10")
        hora_partido = 16 * 60 + 10  # 970 minutos
        print(f"   Hora partido (mins): {hora_partido}")
        print(f"   Fin partido (mins): {hora_partido + 50} (16:10 + 50min = 17:00)")
        
        if restricciones:
            for r in restricciones:
                dias = r.get('dias', [])
                if 'viernes' in dias:
                    hora_inicio = r.get('horaInicio', '00:00')
                    hora_fin = r.get('horaFin', '23:59')
                    inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                    fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                    
                    print(f"\n   Restricción viernes: {hora_inicio} - {hora_fin}")
                    print(f"   Restricción (mins): {inicio_mins} - {fin_mins}")
                    
                    # Verificar solapamiento
                    # Partido: [970, 1020] (16:10 - 17:00)
                    # Restricción: [540, 1140] (09:00 - 19:00)
                    # Solapamiento si: partido_inicio < restriccion_fin AND partido_fin > restriccion_inicio
                    solapa = hora_partido < fin_mins and (hora_partido + 50) > inicio_mins
                    
                    print(f"\n   ¿Hay solapamiento?")
                    print(f"      hora_partido ({hora_partido}) < fin_mins ({fin_mins}): {hora_partido < fin_mins}")
                    print(f"      (hora_partido + 50) ({hora_partido + 50}) > inicio_mins ({inicio_mins}): {(hora_partido + 50) > inicio_mins}")
                    print(f"      Resultado: {solapa}")
                    
                    if solapa:
                        print(f"\n   ❌ NO DISPONIBLE - Hay solapamiento")
                    else:
                        print(f"\n   ✅ DISPONIBLE - No hay solapamiento")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_restricciones()
