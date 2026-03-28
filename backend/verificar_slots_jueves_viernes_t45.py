#!/usr/bin/env python3
"""
Verificar slots disponibles jueves y viernes después de las 22:00 - Torneo 45
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def verificar():
    s = Session()
    try:
        print("=" * 80)
        print(f"SLOTS DISPONIBLES JUEVES Y VIERNES DESPUÉS DE LAS 22:00 - TORNEO {TORNEO_ID}")
        print("=" * 80)

        # Obtener fechas del torneo
        torneo = s.execute(text("""
            SELECT fecha_inicio, fecha_fin FROM torneos WHERE id = :t
        """), {"t": TORNEO_ID}).fetchone()
        
        if not torneo:
            print("\n❌ Torneo no encontrado")
            return
        
        fecha_inicio = torneo[0]
        fecha_fin = torneo[1]
        
        print(f"\n📅 Torneo: {fecha_inicio} al {fecha_fin}")

        # Obtener canchas
        canchas = s.execute(text("""
            SELECT id, nombre FROM torneo_canchas 
            WHERE torneo_id = :t AND activa = true
            ORDER BY nombre
        """), {"t": TORNEO_ID}).fetchall()
        
        print(f"🏟️  Canchas: {', '.join(c.nombre for c in canchas)}")

        # Buscar jueves y viernes en el rango del torneo
        current = fecha_inicio
        jueves_viernes = []
        
        while current <= fecha_fin:
            dow = current.weekday()  # 0=lunes, 3=jueves, 4=viernes
            if dow == 3:  # jueves
                jueves_viernes.append(('jueves', current))
            elif dow == 4:  # viernes
                jueves_viernes.append(('viernes', current))
            current += timedelta(days=1)

        print(f"\n📆 Días encontrados:")
        for dia, fecha in jueves_viernes:
            print(f"   {dia.capitalize()}: {fecha.strftime('%d/%m/%Y')}")

        # Para cada día, verificar slots después de las 22:00
        print(f"\n{'=' * 80}")
        print("SLOTS DISPONIBLES DESPUÉS DE LAS 22:00")
        print("=" * 80)

        for dia_nombre, fecha in jueves_viernes:
            print(f"\n📅 {dia_nombre.upper()} {fecha.strftime('%d/%m/%Y')}")
            print("-" * 80)
            
            # Horarios posibles después de las 22:00
            horarios_posibles = ["22:00", "22:30", "23:00", "23:30", "23:59"]
            
            for hora_str in horarios_posibles:
                hora, minuto = map(int, hora_str.split(':'))
                fecha_hora = datetime(fecha.year, fecha.month, fecha.day, hora, minuto)
                
                # Verificar cada cancha
                slots_libres = []
                for cancha in canchas:
                    # Buscar si hay partido en este slot
                    partido = s.execute(text("""
                        SELECT p.id_partido FROM partidos p
                        JOIN torneos_parejas tp ON p.pareja1_id = tp.id
                        WHERE tp.torneo_id = :t
                        AND p.cancha_id = :c
                        AND p.fecha_hora = :fh
                    """), {"t": TORNEO_ID, "c": cancha.id, "fh": fecha_hora}).fetchone()
                    
                    if not partido:
                        slots_libres.append(cancha.nombre)
                
                if slots_libres:
                    print(f"   ⏰ {hora_str}: {', '.join(slots_libres)} LIBRE{'S' if len(slots_libres) > 1 else ''}")

        print(f"\n{'=' * 80}")
        print("✅ VERIFICACIÓN COMPLETA")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    verificar()
