#!/usr/bin/env python3
"""
Verificar solapamientos simples en torneo 45
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
DURACION_PARTIDO = 50  # minutos

def main():
    s = Session()
    try:
        print("=" * 80)
        print(f"VERIFICAR SOLAPAMIENTOS - TORNEO {TORNEO_ID}")
        print("=" * 80)

        # Obtener todos los partidos con sus parejas
        partidos = s.execute(text("""
            SELECT 
                p.id_partido,
                p.fecha_hora,
                p.cancha_id,
                tc.nombre as categoria,
                tz.nombre as zona,
                tca.nombre as cancha,
                tp1.id as pareja1_id,
                tp2.id as pareja2_id,
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
            LEFT JOIN torneo_categorias tc ON tp1.categoria_id = tc.id
            LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
            LEFT JOIN torneo_canchas tca ON p.cancha_id = tca.id
            WHERE tp1.torneo_id = :t
            AND p.fecha_hora IS NOT NULL
            ORDER BY p.fecha_hora, p.cancha_id
        """), {"t": TORNEO_ID}).fetchall()

        print(f"\n📊 Total partidos programados: {len(partidos)}\n")

        # Agrupar por horario y cancha
        horarios = {}
        for p in partidos:
            key = (p.fecha_hora, p.cancha_id)
            if key not in horarios:
                horarios[key] = []
            horarios[key].append(p)

        # Verificar solapamientos de cancha
        print("=" * 80)
        print("VERIFICAR SOLAPAMIENTOS DE CANCHA")
        print("=" * 80)
        
        solapamientos_cancha = []
        for i, p1 in enumerate(partidos):
            fin_p1 = p1.fecha_hora + timedelta(minutes=DURACION_PARTIDO)
            
            for p2 in partidos[i+1:]:
                # Si es la misma cancha
                if p1.cancha_id == p2.cancha_id:
                    fin_p2 = p2.fecha_hora + timedelta(minutes=DURACION_PARTIDO)
                    
                    # Verificar si se solapan en tiempo
                    if p1.fecha_hora < fin_p2 and p2.fecha_hora < fin_p1:
                        solapamientos_cancha.append((p1, p2))

        if solapamientos_cancha:
            print(f"\n⚠️  {len(solapamientos_cancha)} SOLAPAMIENTOS DE CANCHA DETECTADOS:\n")
            for p1, p2 in solapamientos_cancha:
                print(f"🚨 Partido #{p1.id_partido} y #{p2.id_partido}")
                print(f"   Cancha: {p1.cancha}")
                print(f"   P{p1.id_partido}: {p1.fecha_hora.strftime('%d/%m %H:%M')} - {p1.categoria} {p1.zona}")
                print(f"   P{p2.id_partido}: {p2.fecha_hora.strftime('%d/%m %H:%M')} - {p2.categoria} {p2.zona}")
                print()
        else:
            print("\n✅ No hay solapamientos de cancha\n")

        # Verificar solapamientos de parejas
        print("=" * 80)
        print("VERIFICAR SOLAPAMIENTOS DE PAREJAS")
        print("=" * 80)
        
        solapamientos_pareja = []
        for i, p1 in enumerate(partidos):
            fin_p1 = p1.fecha_hora + timedelta(minutes=DURACION_PARTIDO)
            parejas_p1 = {p1.pareja1_id, p1.pareja2_id}
            
            for p2 in partidos[i+1:]:
                fin_p2 = p2.fecha_hora + timedelta(minutes=DURACION_PARTIDO)
                parejas_p2 = {p2.pareja1_id, p2.pareja2_id}
                
                # Verificar si se solapan en tiempo
                if p1.fecha_hora < fin_p2 and p2.fecha_hora < fin_p1:
                    # Verificar si comparten pareja
                    if parejas_p1 & parejas_p2:
                        solapamientos_pareja.append((p1, p2))

        if solapamientos_pareja:
            print(f"\n⚠️  {len(solapamientos_pareja)} SOLAPAMIENTOS DE PAREJA DETECTADOS:\n")
            for p1, p2 in solapamientos_pareja:
                print(f"🚨 Partido #{p1.id_partido} y #{p2.id_partido}")
                print(f"   P{p1.id_partido}: {p1.fecha_hora.strftime('%d/%m %H:%M')} {p1.cancha} - {p1.categoria} {p1.zona}")
                print(f"   {p1.j1_p1} - {p1.j2_p1} vs {p1.j1_p2} - {p1.j2_p2}")
                print(f"   P{p2.id_partido}: {p2.fecha_hora.strftime('%d/%m %H:%M')} {p2.cancha} - {p2.categoria} {p2.zona}")
                print(f"   {p2.j1_p1} - {p2.j2_p1} vs {p2.j1_p2} - {p2.j2_p2}")
                print()
        else:
            print("\n✅ No hay solapamientos de parejas\n")

        print("=" * 80)
        if not solapamientos_cancha and not solapamientos_pareja:
            print("✅ FIXTURE SIN SOLAPAMIENTOS")
        else:
            print(f"⚠️  TOTAL: {len(solapamientos_cancha) + len(solapamientos_pareja)} SOLAPAMIENTOS")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
