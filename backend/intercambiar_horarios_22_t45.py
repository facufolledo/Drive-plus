#!/usr/bin/env python3
"""
Intercambiar horarios de partidos a las 22:00 según indicaciones del usuario
"""
import sys, os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

# Mapeo de cambios a realizar
CAMBIOS = [
    {
        'descripcion': '6ta - Lucero/Paez: 22:00 jueves → 19:00 jueves',
        'pareja_nombre': 'LUCERO NICLAS -LUCIANO PAEZ',
        'horario_actual': '22:00',
        'dia_actual': 'jueves',
        'nuevo_horario': '19:00',
        'nuevo_dia': 'jueves'
    },
    {
        'descripcion': '4ta - Brizuela/Chumbita: 22:00 viernes → 21:00 viernes',
        'pareja_nombre': 'BRIZUELA ALVARO - CHUMBITA AGUSTIN',
        'horario_actual': '22:00',
        'dia_actual': 'viernes',
        'nuevo_horario': '21:00',
        'nuevo_dia': 'viernes'
    },
    {
        'descripcion': '8va - Brizuela/Ceballo: 22:00 jueves → 21:00 jueves',
        'pareja_nombre': 'BRIZUELA MARTIN - CEBALLO SANTIAGO',
        'horario_actual': '22:00',
        'dia_actual': 'jueves',
        'nuevo_horario': '21:00',
        'nuevo_dia': 'jueves'
    }
]

def main():
    s = Session()
    try:
        print("=" * 80)
        print("INTERCAMBIAR HORARIOS DE PARTIDOS A LAS 22:00")
        print("=" * 80)
        
        for cambio in CAMBIOS:
            print(f"\n{'=' * 80}")
            print(f"📋 {cambio['descripcion']}")
            print(f"{'=' * 80}")
            
            # Buscar la pareja
            pareja = s.execute(text("""
                SELECT id, nombre_pareja
                FROM torneos_parejas
                WHERE torneo_id = :tid
                AND UPPER(nombre_pareja) LIKE :nombre
            """), {
                "tid": TORNEO_ID,
                "nombre": f"%{cambio['pareja_nombre'].upper()}%"
            }).fetchone()
            
            if not pareja:
                print(f"❌ No se encontró la pareja: {cambio['pareja_nombre']}")
                continue
            
            print(f"✅ Pareja encontrada: {pareja.nombre_pareja} (ID={pareja.id})")
            
            # Buscar el partido en el horario actual
            partido = s.execute(text("""
                SELECT 
                    p.id_partido,
                    p.fecha_hora,
                    p.cancha_id,
                    tp1.nombre_pareja as pareja1,
                    tp2.nombre_pareja as pareja2
                FROM partidos p
                JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
                WHERE tp1.torneo_id = :tid
                AND (p.pareja1_id = :pid OR p.pareja2_id = :pid)
                AND EXTRACT(HOUR FROM p.fecha_hora) = :hora
                AND EXTRACT(DOW FROM p.fecha_hora) = :dow
            """), {
                "tid": TORNEO_ID,
                "pid": pareja.id,
                "hora": int(cambio['horario_actual'].split(':')[0]),
                "dow": {'jueves': 4, 'viernes': 5}[cambio['dia_actual']]
            }).fetchone()
            
            if not partido:
                print(f"❌ No se encontró partido en {cambio['dia_actual']} {cambio['horario_actual']}")
                continue
            
            print(f"\n📍 Partido encontrado:")
            print(f"   ID: {partido.id_partido}")
            print(f"   {partido.pareja1} vs {partido.pareja2}")
            print(f"   Horario actual: {partido.fecha_hora.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Cancha: {partido.cancha_id}")
            
            # Calcular nuevo horario
            fecha_actual = partido.fecha_hora
            nueva_hora = int(cambio['nuevo_horario'].split(':')[0])
            nuevos_minutos = int(cambio['nuevo_horario'].split(':')[1]) if ':' in cambio['nuevo_horario'] else 0
            
            # Calcular diferencia de días si cambia el día
            dias_map = {'jueves': 4, 'viernes': 5, 'sabado': 6, 'sábado': 6, 'domingo': 0}
            dia_actual_num = dias_map[cambio['dia_actual']]
            dia_nuevo_num = dias_map[cambio['nuevo_dia']]
            
            diferencia_dias = dia_nuevo_num - dia_actual_num
            
            nueva_fecha = fecha_actual.replace(hour=nueva_hora, minute=nuevos_minutos)
            if diferencia_dias != 0:
                nueva_fecha = nueva_fecha + timedelta(days=diferencia_dias)
            
            print(f"\n🔄 Cambio a realizar:")
            print(f"   De: {fecha_actual.strftime('%Y-%m-%d %H:%M')}")
            print(f"   A:  {nueva_fecha.strftime('%Y-%m-%d %H:%M')}")
            
            # Actualizar
            s.execute(text("""
                UPDATE partidos
                SET fecha_hora = :nueva_fecha
                WHERE id_partido = :pid
            """), {
                "nueva_fecha": nueva_fecha,
                "pid": partido.id_partido
            })
            
            print(f"✅ Partido actualizado")
        
        s.commit()
        
        print(f"\n{'=' * 80}")
        print("✅ TODOS LOS CAMBIOS COMPLETADOS")
        print(f"{'=' * 80}")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
