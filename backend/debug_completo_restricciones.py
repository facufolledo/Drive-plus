"""
Debug COMPLETO del flujo de restricciones
Verificar EXACTAMENTE qué está pasando
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def debug_completo():
    session = Session()
    
    try:
        print("=" * 80)
        print("DEBUG COMPLETO: RESTRICCIONES HORARIAS")
        print("=" * 80)
        
        # 1. Ver restricciones de Matias Giordano / Damian Tapia
        print("\n1️⃣ RESTRICCIONES EN BASE DE DATOS:")
        print("=" * 80)
        
        pareja = session.execute(
            text("""
                SELECT 
                    tp.id,
                    tp.disponibilidad_horaria,
                    u1.nombre_usuario as j1,
                    u2.nombre_usuario as j2
                FROM torneos_parejas tp
                JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
                JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
                WHERE tp.torneo_id = 37
                AND (u1.nombre_usuario LIKE '%giordano%' OR u2.nombre_usuario LIKE '%giordano%')
            """)
        ).fetchone()
        
        if pareja:
            print(f"\n🎾 Pareja #{pareja[0]}: {pareja[2]} / {pareja[3]}")
            print(f"\n📋 Restricciones RAW en DB:")
            print(json.dumps(pareja[1], indent=2))
            
            # Parsear restricciones
            restricciones = pareja[1]
            if restricciones:
                print(f"\n🔍 PARSEANDO RESTRICCIONES:")
                for idx, r in enumerate(restricciones):
                    print(f"\n   Restricción {idx + 1}:")
                    print(f"      dias: {r.get('dias', [])}")
                    print(f"      horaInicio: {r.get('horaInicio', 'N/A')}")
                    print(f"      horaFin: {r.get('horaFin', 'N/A')}")
                    
                    # Convertir a minutos
                    hora_inicio = r.get('horaInicio', '00:00')
                    hora_fin = r.get('horaFin', '23:59')
                    inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                    fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                    
                    print(f"      Minutos: {inicio_mins} - {fin_mins}")
                    print(f"      Interpretación: NO puede jugar {r.get('dias', [])} de {hora_inicio} a {hora_fin}")
        
        # 2. Ver partidos programados para esta pareja
        print(f"\n\n2️⃣ PARTIDOS PROGRAMADOS:")
        print("=" * 80)
        
        partidos = session.execute(
            text("""
                SELECT 
                    p.id_partido,
                    p.fecha_hora,
                    p.cancha_id,
                    tc.nombre as cancha,
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
                LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
                WHERE p.id_torneo = 37
                AND (
                    u1.nombre_usuario LIKE '%giordano%' OR 
                    u2.nombre_usuario LIKE '%giordano%' OR
                    u3.nombre_usuario LIKE '%giordano%' OR 
                    u4.nombre_usuario LIKE '%giordano%'
                )
                ORDER BY p.fecha_hora
            """)
        ).fetchall()
        
        if partidos:
            for partido in partidos:
                fecha_hora = partido[1]
                dia_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'][fecha_hora.weekday()]
                hora_mins = fecha_hora.hour * 60 + fecha_hora.minute
                
                print(f"\n🎾 Partido #{partido[0]}")
                print(f"   {partido[4]}/{partido[5]} vs {partido[6]}/{partido[7]}")
                print(f"   📅 {fecha_hora.strftime('%Y-%m-%d %A %H:%M')}")
                print(f"   📍 {dia_semana} a las {fecha_hora.hour:02d}:{fecha_hora.minute:02d} ({hora_mins} mins)")
                print(f"   🏟️  {partido[3]}")
                
                # Verificar si viola restricciones
                if pareja and pareja[1]:
                    print(f"\n   🔍 VERIFICANDO RESTRICCIONES:")
                    for r in pareja[1]:
                        dias = r.get('dias', [])
                        hora_inicio = r.get('horaInicio', '00:00')
                        hora_fin = r.get('horaFin', '23:59')
                        inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                        fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                        
                        if dia_semana in dias:
                            print(f"      Restricción: {dias} {hora_inicio}-{hora_fin} ({inicio_mins}-{fin_mins} mins)")
                            
                            # Verificar solapamiento
                            partido_fin = hora_mins + 50
                            if hora_mins < fin_mins and partido_fin > inicio_mins:
                                print(f"      ❌ VIOLACIÓN DETECTADA!")
                                print(f"         Partido: {hora_mins}-{partido_fin} mins")
                                print(f"         Restricción: {inicio_mins}-{fin_mins} mins")
                                print(f"         Condición: {hora_mins} < {fin_mins} AND {partido_fin} > {inicio_mins}")
                                print(f"         Resultado: {hora_mins < fin_mins} AND {partido_fin > inicio_mins} = TRUE")
                            else:
                                print(f"      ✅ Sin solapamiento")
                                print(f"         Partido: {hora_mins}-{partido_fin} mins")
                                print(f"         Restricción: {inicio_mins}-{fin_mins} mins")
        
        # 3. Simular el parseo del backend
        print(f"\n\n3️⃣ SIMULACIÓN DEL PARSEO DEL BACKEND:")
        print("=" * 80)
        
        if pareja and pareja[1]:
            restricciones_raw = pareja[1]
            
            print(f"\n📥 Input: {type(restricciones_raw)}")
            print(json.dumps(restricciones_raw, indent=2))
            
            # Simular el parseo
            franjas_restricciones = []
            
            if isinstance(restricciones_raw, list):
                franjas_restricciones = restricciones_raw
                print(f"\n✅ Es lista → franjas_restricciones = restricciones_raw")
            elif isinstance(restricciones_raw, dict):
                if 'franjas' in restricciones_raw:
                    franjas_restricciones = restricciones_raw['franjas']
                    print(f"\n✅ Es dict con 'franjas' → franjas_restricciones = restricciones_raw['franjas']")
                else:
                    print(f"\n⚠️  Es dict SIN 'franjas' → franjas_restricciones = []")
            
            print(f"\n📤 Output: {len(franjas_restricciones)} franjas")
            
            # Procesar franjas
            restricciones_por_dia = {}
            for idx, franja in enumerate(franjas_restricciones):
                print(f"\n   Franja {idx + 1}:")
                print(f"      Raw: {franja}")
                
                dias = franja.get('dias', [])
                hora_inicio = franja.get('horaInicio', '00:00')
                hora_fin = franja.get('horaFin', '23:59')
                
                inicio_mins = int(hora_inicio.split(':')[0]) * 60 + int(hora_inicio.split(':')[1])
                fin_mins = int(hora_fin.split(':')[0]) * 60 + int(hora_fin.split(':')[1])
                
                for dia in dias:
                    dia_norm = str(dia).strip().lower()
                    if dia_norm not in restricciones_por_dia:
                        restricciones_por_dia[dia_norm] = []
                    restricciones_por_dia[dia_norm].append((inicio_mins, fin_mins))
                    print(f"      ✅ {dia_norm}: ({inicio_mins}, {fin_mins})")
            
            print(f"\n📊 RESULTADO FINAL:")
            print(f"   restricciones_por_dia = {restricciones_por_dia}")
            
            # Verificar viernes 12:00
            print(f"\n\n4️⃣ VERIFICACIÓN: ¿Puede jugar viernes 12:00?")
            print("=" * 80)
            
            dia_test = 'viernes'
            hora_test = 12 * 60  # 12:00 = 720 mins
            
            print(f"\n   Día: {dia_test}")
            print(f"   Hora: 12:00 ({hora_test} mins)")
            print(f"   Fin partido: 12:50 ({hora_test + 50} mins)")
            
            if dia_test not in restricciones_por_dia:
                print(f"\n   ✅ Día sin restricciones → PUEDE JUGAR")
            else:
                print(f"\n   Restricciones en {dia_test}: {restricciones_por_dia[dia_test]}")
                
                puede_jugar = True
                for inicio_mins, fin_mins in restricciones_por_dia[dia_test]:
                    print(f"\n      Verificando restricción {inicio_mins}-{fin_mins}:")
                    print(f"         Condición: {hora_test} < {fin_mins} AND {hora_test + 50} > {inicio_mins}")
                    print(f"         Resultado: {hora_test < fin_mins} AND {hora_test + 50 > inicio_mins}")
                    
                    if hora_test < fin_mins and (hora_test + 50) > inicio_mins:
                        print(f"         ❌ HAY SOLAPAMIENTO → NO PUEDE JUGAR")
                        puede_jugar = False
                    else:
                        print(f"         ✅ Sin solapamiento")
                
                if puede_jugar:
                    print(f"\n   ✅ RESULTADO: PUEDE JUGAR")
                else:
                    print(f"\n   ❌ RESULTADO: NO PUEDE JUGAR")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_completo()
