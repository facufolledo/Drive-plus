"""
Test de generación de fixture del torneo 37 con el algoritmo corregido
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.services.torneo_fixture_global_service import TorneoFixtureGlobalService

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def test_generar_fixture():
    """Genera fixture del torneo 37 y verifica restricciones"""
    session = Session()
    
    try:
        print("=" * 80)
        print("TEST: GENERACIÓN DE FIXTURE TORNEO 37")
        print("=" * 80)
        
        # Obtener el ID del creador del torneo
        from sqlalchemy import text
        torneo = session.execute(
            text("SELECT creado_por FROM torneos WHERE id = 37")
        ).fetchone()
        
        if not torneo:
            print("❌ Torneo 37 no encontrado")
            return
        
        user_id = torneo[0]
        print(f"\n👤 Usuario creador: {user_id}")
        
        print("\n🔄 Generando fixture para categoría 7ma (ID 85)...")
        
        # Generar fixture solo para categoría 7ma
        resultado = TorneoFixtureGlobalService.generar_fixture_completo(
            db=session,
            torneo_id=37,
            user_id=user_id,
            categoria_id=85  # 7ma
        )
        
        print(f"\n✅ FIXTURE GENERADO:")
        print(f"   • Partidos programados: {resultado['partidos_generados']}")
        print(f"   • Partidos NO programados: {resultado['partidos_no_programados']}")
        print(f"   • Zonas procesadas: {resultado['zonas_procesadas']}")
        print(f"   • Canchas utilizadas: {resultado['canchas_utilizadas']}")
        print(f"   • Slots utilizados: {resultado['slots_utilizados']}")
        
        if resultado['partidos_no_programados'] > 0:
            print(f"\n⚠️  PARTIDOS NO PROGRAMADOS:")
            for partido in resultado['partidos_sin_programar']:
                print(f"\n   🎾 {partido['pareja1_nombre']} vs {partido['pareja2_nombre']}")
                print(f"      Categoría: {partido['categoria_nombre']}")
                print(f"      Motivo: {partido['motivo']}")
                print(f"      Pareja 1: {partido['disponibilidad_pareja1']}")
                print(f"      Pareja 2: {partido['disponibilidad_pareja2']}")
        
        # Verificar restricciones
        print(f"\n{'=' * 80}")
        print(f"VERIFICANDO RESTRICCIONES...")
        print(f"{'=' * 80}")
        
        from sqlalchemy import text
        
        partidos = session.execute(
            text("""
                SELECT 
                    p.id_partido,
                    p.fecha_hora,
                    tp1.id as pareja1_id,
                    tp1.disponibilidad_horaria as pareja1_restricciones,
                    tp2.id as pareja2_id,
                    tp2.disponibilidad_horaria as pareja2_restricciones,
                    u1.nombre_usuario as j1_p1,
                    u2.nombre_usuario as j2_p1,
                    u3.nombre_usuario as j1_p2,
                    u4.nombre_usuario as j2_p2
                FROM partidos p
                JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
                JOIN usuarios u1 ON tp1.jugador1_id = u1.id_usuario
                JOIN usuarios u2 ON tp1.jugador2_id = u2.id_usuario
                JOIN usuarios u3 ON tp2.jugador1_id = u3.id_usuario
                JOIN usuarios u4 ON tp2.jugador2_id = u4.id_usuario
                WHERE p.id_torneo = 37 AND p.categoria_id = 85
                ORDER BY p.fecha_hora
            """)
        ).fetchall()
        
        violaciones = 0
        
        for partido in partidos:
            fecha_hora = partido[1]
            pareja1_restricciones = partido[3]
            pareja2_restricciones = partido[5]
            j1_p1 = partido[6]
            j2_p1 = partido[7]
            j1_p2 = partido[8]
            j2_p2 = partido[9]
            
            dia_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'][fecha_hora.weekday()]
            hora_mins = fecha_hora.hour * 60 + fecha_hora.minute
            
            # Verificar pareja 1
            if pareja1_restricciones:
                for restriccion in pareja1_restricciones:
                    dias = restriccion.get('dias', [])
                    hora_inicio = restriccion.get('horaInicio', '00:00')
                    hora_fin = restriccion.get('horaFin', '23:59')
                    
                    inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                    fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                    
                    if dia_semana in dias:
                        if hora_mins < fin_mins and (hora_mins + 50) > inicio_mins:
                            print(f"\n❌ VIOLACIÓN: {j1_p1}/{j2_p1} jugando {dia_semana} {fecha_hora.strftime('%H:%M')}")
                            print(f"   Restricción: NO puede {dia_semana} {hora_inicio}-{hora_fin}")
                            violaciones += 1
            
            # Verificar pareja 2
            if pareja2_restricciones:
                for restriccion in pareja2_restricciones:
                    dias = restriccion.get('dias', [])
                    hora_inicio = restriccion.get('horaInicio', '00:00')
                    hora_fin = restriccion.get('horaFin', '23:59')
                    
                    inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                    fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                    
                    if dia_semana in dias:
                        if hora_mins < fin_mins and (hora_mins + 50) > inicio_mins:
                            print(f"\n❌ VIOLACIÓN: {j1_p2}/{j2_p2} jugando {dia_semana} {fecha_hora.strftime('%H:%M')}")
                            print(f"   Restricción: NO puede {dia_semana} {hora_inicio}-{hora_fin}")
                            violaciones += 1
        
        print(f"\n{'=' * 80}")
        if violaciones == 0:
            print(f"✅ TODAS LAS RESTRICCIONES SE RESPETAN CORRECTAMENTE")
        else:
            print(f"❌ SE ENCONTRARON {violaciones} VIOLACIONES")
        print(f"{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_generar_fixture()
