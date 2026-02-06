"""
Test de generación de fixture del torneo 37 con restricciones horarias
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def test_fixture_restricciones():
    """Verifica que el fixture respete las restricciones horarias"""
    session = Session()
    
    try:
        print("=" * 80)
        print("TEST: FIXTURE TORNEO 37 - VERIFICACIÓN DE RESTRICCIONES")
        print("=" * 80)
        
        # Obtener partidos programados
        partidos = session.execute(
            text("""
                SELECT 
                    p.id_partido,
                    p.fecha_hora,
                    p.cancha_id,
                    tp1.id as pareja1_id,
                    tp1.disponibilidad_horaria as pareja1_restricciones,
                    tp2.id as pareja2_id,
                    tp2.disponibilidad_horaria as pareja2_restricciones,
                    u1.nombre_usuario as j1_p1,
                    u2.nombre_usuario as j2_p1,
                    u3.nombre_usuario as j1_p2,
                    u4.nombre_usuario as j2_p2,
                    tc.nombre as cancha_nombre,
                    tcat.nombre as categoria
                FROM partidos p
                JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
                JOIN usuarios u1 ON tp1.jugador1_id = u1.id_usuario
                JOIN usuarios u2 ON tp1.jugador2_id = u2.id_usuario
                JOIN usuarios u3 ON tp2.jugador1_id = u3.id_usuario
                JOIN usuarios u4 ON tp2.jugador2_id = u4.id_usuario
                LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
                LEFT JOIN torneo_categorias tcat ON p.categoria_id = tcat.id
                WHERE p.id_torneo = 37
                ORDER BY p.fecha_hora, tc.nombre
            """)
        ).fetchall()
        
        if not partidos:
            print("\n⚠️  No hay partidos programados")
            print("   Genera el fixture desde el frontend primero")
            return
        
        print(f"\n📊 PARTIDOS PROGRAMADOS: {len(partidos)}")
        print("=" * 80)
        
        violaciones = []
        partidos_por_jugador = {}
        
        for partido in partidos:
            partido_id = partido[0]
            fecha_hora = partido[1]
            cancha_nombre = partido[11]
            categoria = partido[12]
            
            pareja1_id = partido[3]
            pareja1_restricciones = partido[4]
            pareja2_id = partido[5]
            pareja2_restricciones = partido[6]
            
            j1_p1 = partido[7]
            j2_p1 = partido[8]
            j1_p2 = partido[9]
            j2_p2 = partido[10]
            
            # Obtener día y hora
            dia_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'][fecha_hora.weekday()]
            hora_mins = fecha_hora.hour * 60 + fecha_hora.minute
            
            print(f"\n🎾 Partido #{partido_id} - {categoria}")
            print(f"   {j1_p1}/{j2_p1} vs {j1_p2}/{j2_p2}")
            print(f"   📅 {fecha_hora.strftime('%Y-%m-%d %A %H:%M')} ({dia_semana})")
            print(f"   🏟️  {cancha_nombre}")
            
            # Verificar restricciones pareja 1
            if pareja1_restricciones:
                for restriccion in pareja1_restricciones:
                    dias = restriccion.get('dias', [])
                    hora_inicio = restriccion.get('horaInicio', '00:00')
                    hora_fin = restriccion.get('horaFin', '23:59')
                    
                    inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                    fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                    
                    if dia_semana in dias:
                        # Verificar solapamiento
                        if hora_mins < fin_mins and (hora_mins + 50) > inicio_mins:
                            violacion = f"❌ VIOLACIÓN: Pareja {j1_p1}/{j2_p1} NO puede jugar {dia_semana} {hora_inicio}-{hora_fin}"
                            print(f"   {violacion}")
                            violaciones.append({
                                'partido_id': partido_id,
                                'pareja': f"{j1_p1}/{j2_p1}",
                                'fecha_hora': fecha_hora,
                                'restriccion': f"{dia_semana} {hora_inicio}-{hora_fin}",
                                'violacion': violacion
                            })
            
            # Verificar restricciones pareja 2
            if pareja2_restricciones:
                for restriccion in pareja2_restricciones:
                    dias = restriccion.get('dias', [])
                    hora_inicio = restriccion.get('horaInicio', '00:00')
                    hora_fin = restriccion.get('horaFin', '23:59')
                    
                    inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                    fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                    
                    if dia_semana in dias:
                        # Verificar solapamiento
                        if hora_mins < fin_mins and (hora_mins + 50) > inicio_mins:
                            violacion = f"❌ VIOLACIÓN: Pareja {j1_p2}/{j2_p2} NO puede jugar {dia_semana} {hora_inicio}-{hora_fin}"
                            print(f"   {violacion}")
                            violaciones.append({
                                'partido_id': partido_id,
                                'pareja': f"{j1_p2}/{j2_p2}",
                                'fecha_hora': fecha_hora,
                                'restriccion': f"{dia_semana} {hora_inicio}-{hora_fin}",
                                'violacion': violacion
                            })
            
            # Verificar tiempo mínimo entre partidos (3 horas)
            jugadores = [j1_p1, j2_p1, j1_p2, j2_p2]
            for jugador in jugadores:
                if jugador in partidos_por_jugador:
                    for fecha_hora_anterior in partidos_por_jugador[jugador]:
                        diferencia_minutos = abs((fecha_hora - fecha_hora_anterior).total_seconds() / 60)
                        if diferencia_minutos < 180:
                            violacion = f"⚠️  ADVERTENCIA: {jugador} juega con menos de 3 horas de diferencia ({diferencia_minutos:.0f} min)"
                            print(f"   {violacion}")
                            violaciones.append({
                                'partido_id': partido_id,
                                'jugador': jugador,
                                'fecha_hora': fecha_hora,
                                'fecha_hora_anterior': fecha_hora_anterior,
                                'diferencia_minutos': diferencia_minutos,
                                'violacion': violacion
                            })
                else:
                    partidos_por_jugador[jugador] = []
                
                partidos_por_jugador[jugador].append(fecha_hora)
        
        # Resumen
        print(f"\n{'=' * 80}")
        print(f"RESUMEN:")
        print(f"   • Total partidos: {len(partidos)}")
        print(f"   • Violaciones encontradas: {len(violaciones)}")
        
        if violaciones:
            print(f"\n❌ SE ENCONTRARON VIOLACIONES:")
            for v in violaciones:
                print(f"   • {v['violacion']}")
        else:
            print(f"\n✅ TODAS LAS RESTRICCIONES SE RESPETAN CORRECTAMENTE")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_fixture_restricciones()
