#!/usr/bin/env python3
"""
Verificar solapamientos en el torneo 45
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import timedelta

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45
DURACION_PARTIDO = 50  # minutos

def verificar():
    s = Session()
    try:
        print("=" * 80)
        print(f"VERIFICAR SOLAPAMIENTOS - TORNEO {TORNEO_ID}")
        print("=" * 80)

        # Obtener todos los partidos programados
        partidos = s.execute(text("""
            SELECT 
                p.id_partido,
                p.fecha_hora,
                p.cancha_id,
                tc.nombre as categoria,
                tz.nombre as zona,
                tca.nombre as cancha,
                tp1.id as pareja1_id,
                tp2.id as pareja2_id
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            LEFT JOIN torneo_categorias tc ON tp1.categoria_id = tc.id
            LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
            LEFT JOIN torneo_canchas tca ON p.cancha_id = tca.id
            WHERE tp1.torneo_id = :t
            AND p.fecha_hora IS NOT NULL
            ORDER BY p.fecha_hora
        """), {"t": TORNEO_ID}).fetchall()

        if not partidos:
            print("\n✅ No hay partidos programados")
            return

        print(f"\n📊 Total partidos: {len(partidos)}")
        print(f"⏱️  Duración estimada: {DURACION_PARTIDO} minutos\n")

        solapamientos = []

        # Verificar solapamientos
        for i, p1 in enumerate(partidos):
            fin_p1 = p1.fecha_hora + timedelta(minutes=DURACION_PARTIDO)
            
            for p2 in partidos[i+1:]:
                fin_p2 = p2.fecha_hora + timedelta(minutes=DURACION_PARTIDO)
                
                # Verificar si se solapan en tiempo
                if p1.fecha_hora < fin_p2 and p2.fecha_hora < fin_p1:
                    # Solapamiento de cancha
                    if p1.cancha_id == p2.cancha_id:
                        solapamientos.append({
                            "tipo": "cancha",
                            "p1": p1,
                            "p2": p2,
                            "mensaje": f"Misma cancha ({p1.cancha}) en horarios solapados"
                        })
                    
                    # Solapamiento de pareja
                    parejas_p1 = {p1.pareja1_id, p1.pareja2_id}
                    parejas_p2 = {p2.pareja1_id, p2.pareja2_id}
                    
                    if parejas_p1 & parejas_p2:  # Intersección
                        solapamientos.append({
                            "tipo": "pareja",
                            "p1": p1,
                            "p2": p2,
                            "mensaje": "Pareja juega en dos partidos al mismo tiempo"
                        })

        if not solapamientos:
            print("=" * 80)
            print("✅ NO SE DETECTARON SOLAPAMIENTOS")
            print("=" * 80)
            return

        print("=" * 80)
        print(f"⚠️  SE DETECTARON {len(solapamientos)} SOLAPAMIENTOS")
        print("=" * 80)

        for idx, solap in enumerate(solapamientos, 1):
            p1 = solap["p1"]
            p2 = solap["p2"]
            
            print(f"\n🚨 SOLAPAMIENTO #{idx} - {solap['tipo'].upper()}")
            print(f"   {solap['mensaje']}")
            print(f"\n   Partido #{p1.id_partido}:")
            print(f"   📅 {p1.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
            print(f"   🏟️  {p1.cancha}")
            print(f"   📍 {p1.categoria} - {p1.zona}")
            
            print(f"\n   Partido #{p2.id_partido}:")
            print(f"   📅 {p2.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
            print(f"   🏟️  {p2.cancha}")
            print(f"   📍 {p2.categoria} - {p2.zona}")
            print()

        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    verificar()
