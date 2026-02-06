"""
Debug detallado de restricciones - Verificar qué está pasando
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

def debug_partido_especifico():
    """Debug de un partido específico que viola restricciones"""
    session = Session()
    
    try:
        print("=" * 80)
        print("DEBUG: PARTIDO CON RESTRICCIONES VIOLADAS")
        print("=" * 80)
        
        # Buscar partidos del viernes 16:10
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
                    u4.nombre_usuario as j2_p2
                FROM partidos p
                JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
                JOIN usuarios u1 ON tp1.jugador1_id = u1.id_usuario
                JOIN usuarios u2 ON tp1.jugador2_id = u2.id_usuario
                JOIN usuarios u3 ON tp2.jugador1_id = u3.id_usuario
                JOIN usuarios u4 ON tp2.jugador2_id = u4.id_usuario
                WHERE p.id_torneo = 37
                AND EXTRACT(HOUR FROM p.fecha_hora) = 16
                AND EXTRACT(MINUTE FROM p.fecha_hora) = 10
            """)
        ).fetchall()
        
        if not partidos:
            print("\n✅ No hay partidos a las 16:10")
            print("   El problema puede estar resuelto")
            return
        
        print(f"\n⚠️  PARTIDOS ENCONTRADOS A LAS 16:10: {len(partidos)}")
        
        for partido in partidos:
            print(f"\n{'=' * 80}")
            print(f"🎾 Partido #{partido[0]}")
            print(f"   Fecha/Hora: {partido[1]}")
            print(f"   Cancha: {partido[2]}")
            print(f"\n   Pareja 1 (ID {partido[3]}): {partido[7]}/{partido[8]}")
            print(f"   Restricciones: {partido[4]}")
            
            print(f"\n   Pareja 2 (ID {partido[5]}): {partido[9]}/{partido[10]}")
            print(f"   Restricciones: {partido[6]}")
            
            # Verificar si viernes 16:10 está en las restricciones
            fecha_hora = partido[1]
            dia_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'][fecha_hora.weekday()]
            hora_mins = fecha_hora.hour * 60 + fecha_hora.minute
            
            print(f"\n   📅 Día: {dia_semana}")
            print(f"   ⏰ Hora: {fecha_hora.hour:02d}:{fecha_hora.minute:02d} ({hora_mins} mins)")
            print(f"   ⏱️  Fin partido: {(hora_mins + 50) // 60:02d}:{(hora_mins + 50) % 60:02d} ({hora_mins + 50} mins)")
            
            # Verificar pareja 1
            if partido[4]:
                print(f"\n   🔍 VERIFICANDO PAREJA 1:")
                for restriccion in partido[4]:
                    dias = restriccion.get('dias', [])
                    hora_inicio = restriccion.get('horaInicio', '00:00')
                    hora_fin = restriccion.get('horaFin', '23:59')
                    
                    inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                    fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                    
                    if dia_semana in dias:
                        print(f"      Restricción: {dias} {hora_inicio}-{hora_fin} ({inicio_mins}-{fin_mins} mins)")
                        
                        # Verificar solapamiento
                        if hora_mins < fin_mins and (hora_mins + 50) > inicio_mins:
                            print(f"      ❌ VIOLACIÓN DETECTADA!")
                            print(f"         Partido: {hora_mins}-{hora_mins + 50}")
                            print(f"         Restricción: {inicio_mins}-{fin_mins}")
                            print(f"         Solapamiento: {hora_mins} < {fin_mins} AND {hora_mins + 50} > {inicio_mins}")
                        else:
                            print(f"      ✅ Sin solapamiento")
            
            # Verificar pareja 2
            if partido[6]:
                print(f"\n   🔍 VERIFICANDO PAREJA 2:")
                for restriccion in partido[6]:
                    dias = restriccion.get('dias', [])
                    hora_inicio = restriccion.get('horaInicio', '00:00')
                    hora_fin = restriccion.get('horaFin', '23:59')
                    
                    inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                    fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                    
                    if dia_semana in dias:
                        print(f"      Restricción: {dias} {hora_inicio}-{hora_fin} ({inicio_mins}-{fin_mins} mins)")
                        
                        # Verificar solapamiento
                        if hora_mins < fin_mins and (hora_mins + 50) > inicio_mins:
                            print(f"      ❌ VIOLACIÓN DETECTADA!")
                            print(f"         Partido: {hora_mins}-{hora_mins + 50}")
                            print(f"         Restricción: {inicio_mins}-{fin_mins}")
                            print(f"         Solapamiento: {hora_mins} < {fin_mins} AND {hora_mins + 50} > {inicio_mins}")
                        else:
                            print(f"      ✅ Sin solapamiento")
        
        print(f"\n{'=' * 80}")
        print("\n💡 CONCLUSIÓN:")
        print("   Si ves violaciones arriba, el backend NO está usando el código corregido")
        print("   Solución: Reiniciar el backend completamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_partido_especifico()
