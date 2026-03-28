#!/usr/bin/env python3
"""
Listar todos los partidos agrupados por hora en torneo 45
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from collections import defaultdict

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def main():
    s = Session()
    try:
        print("=" * 80)
        print(f"PARTIDOS POR HORA - TORNEO {TORNEO_ID}")
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

        if not partidos:
            print("\n❌ No hay partidos programados")
            return

        print(f"\n📊 Total: {len(partidos)} partidos programados\n")

        # Agrupar por fecha y hora
        por_horario = defaultdict(list)
        for p in partidos:
            # Agrupar por día y hora
            key = p.fecha_hora.strftime("%A %d/%m/%Y - %H:%M")
            por_horario[key].append(p)

        # Días en español
        dias = {
            "Monday": "Lunes",
            "Tuesday": "Martes", 
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo"
        }

        # Mostrar agrupados
        for horario in sorted(por_horario.keys()):
            # Traducir día
            horario_es = horario
            for en, es in dias.items():
                horario_es = horario_es.replace(en, es)
            
            partidos_horario = por_horario[horario]
            print("=" * 80)
            print(f"📅 {horario_es}")
            print(f"🏐 {len(partidos_horario)} partidos")
            print("=" * 80)
            
            for p in partidos_horario:
                print(f"\n🏐 Partido #{p.id_partido}")
                print(f"   🏟️  {p.cancha}")
                print(f"   📍 {p.categoria} - {p.zona}")
                print(f"   👥 {p.j1_p1} - {p.j2_p1}")
                print(f"   vs")
                print(f"   👥 {p.j1_p2} - {p.j2_p2}")
            
            print()

        # Resumen por día
        print("=" * 80)
        print("RESUMEN POR DÍA")
        print("=" * 80)
        
        por_dia = defaultdict(int)
        for p in partidos:
            dia = p.fecha_hora.strftime("%A %d/%m/%Y")
            # Traducir
            for en, es in dias.items():
                dia = dia.replace(en, es)
            por_dia[dia] += 1
        
        for dia in sorted(por_dia.keys()):
            print(f"📅 {dia}: {por_dia[dia]} partidos")

        # Resumen por cancha
        print("\n" + "=" * 80)
        print("RESUMEN POR CANCHA")
        print("=" * 80)
        
        por_cancha = defaultdict(int)
        for p in partidos:
            por_cancha[p.cancha] += 1
        
        for cancha in sorted(por_cancha.keys()):
            print(f"🏟️  {cancha}: {por_cancha[cancha]} partidos")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
