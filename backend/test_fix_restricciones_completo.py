"""
Test completo del fix de restricciones horarias
Verifica que el parseo y validación funcionen correctamente
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def test_parseo_restricciones():
    """Test del parseo de restricciones"""
    from src.services.torneo_fixture_global_service import TorneoFixtureGlobalService
    from src.models.torneo_models import TorneoPareja, Torneo
    
    session = Session()
    
    try:
        print("=" * 80)
        print("TEST: PARSEO DE RESTRICCIONES")
        print("=" * 80)
        
        # Obtener torneo 37
        torneo = session.query(Torneo).filter(Torneo.id == 37).first()
        if not torneo:
            print("❌ Torneo 37 no encontrado")
            return
        
        # Obtener parejas con restricciones
        parejas = session.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == 37,
            TorneoPareja.disponibilidad_horaria.isnot(None)
        ).all()
        
        print(f"\n📊 Parejas con restricciones: {len(parejas)}")
        
        # Simular partidos para probar el parseo
        partidos_test = []
        for pareja in parejas[:2]:  # Solo las primeras 2 para el test
            partidos_test.append({
                'pareja1_id': pareja.id,
                'pareja2_id': pareja.id + 1
            })
        
        # Llamar al método de parseo
        print("\n🔍 Ejecutando _obtener_disponibilidad_parejas...")
        resultado = TorneoFixtureGlobalService._obtener_disponibilidad_parejas(
            session, partidos_test, torneo
        )
        
        print(f"\n✅ Parseo completado")
        print(f"   Parejas procesadas: {len(resultado)}")
        
        # Verificar que todas tengan la estructura correcta
        for pareja_id, datos in resultado.items():
            if 'restricciones_por_dia' not in datos:
                print(f"   ❌ Pareja {pareja_id}: Falta 'restricciones_por_dia'")
            else:
                restricciones = datos['restricciones_por_dia']
                print(f"   ✅ Pareja {pareja_id}: {len(restricciones)} días con restricciones")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def test_verificacion_disponibilidad():
    """Test de la verificación de disponibilidad"""
    from src.services.torneo_fixture_global_service import TorneoFixtureGlobalService
    
    print("\n" + "=" * 80)
    print("TEST: VERIFICACIÓN DE DISPONIBILIDAD")
    print("=" * 80)
    
    # Caso 1: Sin restricciones
    datos_sin_restricciones = {'restricciones_por_dia': {}}
    resultado = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
        'viernes', 970, datos_sin_restricciones
    )
    print(f"\n✅ Sin restricciones → {resultado} (esperado: True)")
    
    # Caso 2: Con restricción que NO solapa
    datos_con_restriccion = {
        'restricciones_por_dia': {
            'viernes': [(540, 900)]  # 09:00-15:00
        }
    }
    resultado = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
        'viernes', 970, datos_con_restriccion  # 16:10
    )
    print(f"\n✅ Restricción 09:00-15:00, partido 16:10 → {resultado} (esperado: True)")
    
    # Caso 3: Con restricción que SÍ solapa
    datos_con_restriccion_solapa = {
        'restricciones_por_dia': {
            'viernes': [(540, 1140)]  # 09:00-19:00
        }
    }
    resultado = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
        'viernes', 970, datos_con_restriccion_solapa  # 16:10
    )
    print(f"\n✅ Restricción 09:00-19:00, partido 16:10 → {resultado} (esperado: False)")
    
    # Caso 4: Día sin restricciones
    resultado = TorneoFixtureGlobalService._verificar_disponibilidad_pareja(
        'sabado', 970, datos_con_restriccion_solapa
    )
    print(f"\n✅ Restricción solo viernes, partido sábado → {resultado} (esperado: True)")
    
    print(f"\n{'=' * 80}")

if __name__ == "__main__":
    test_parseo_restricciones()
    test_verificacion_disponibilidad()
    
    print("\n" + "=" * 80)
    print("TESTS COMPLETADOS")
    print("=" * 80)
    print("\nAhora puedes:")
    print("1. Eliminar el fixture del torneo 37: python backend/limpiar_fixture_torneo37.py")
    print("2. Generar nuevo fixture desde el frontend")
    print("3. Verificar restricciones: python backend/test_fixture_torneo37_restricciones.py")
