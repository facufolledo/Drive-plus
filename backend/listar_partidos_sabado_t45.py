#!/usr/bin/env python3
"""
Listar partidos del sábado después de las 15:00 - Torneo 45
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def listar():
    s = Session()
    try:
        print("=" * 80)
        print(f"PARTIDOS DEL SÁBADO DESPUÉS DE LAS 15:00 - TORNEO {TORNEO_ID}")
        print("=" * 80)

        # Obtener partidos del sábado después de las 15:00
        partidos = s.execute(text("""
            SELECT 
                p.id_partido,
                p.fecha_hora,
                tc.nombre as categoria,
                tz.nombre as zona,
                u1.nombre_usuario as jugador1_p1,
                u2.nombre_usuario as jugador2_p1,
                u3.nombre_usuario as jugador1_p2,
                u4.nombre_usuario as jugador2_p2,
                tca.nombre as cancha
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
            AND EXTRACT(DOW FROM p.fecha_hora) = 6
            AND EXTRACT(HOUR FROM p.fecha_hora) >= 14
            ORDER BY p.fecha_hora, tc.nombre, tz.nombre
        """), {"t": TORNEO_ID}).fetchall()

        if not partidos:
            print("\n✅ No hay partidos programados el sábado después de las 15:00")
            return

        print(f"\n📋 Total: {len(partidos)} partidos\n")

        # Agrupar por categoría
        por_categoria = {}
        for p in partidos:
            cat = p.categoria or "Sin categoría"
            if cat not in por_categoria:
                por_categoria[cat] = []
            por_categoria[cat].append(p)

        # Mostrar por categoría
        for cat, partidos_cat in sorted(por_categoria.items()):
            print(f"\n{'=' * 80}")
            print(f"📌 {cat.upper()}")
            print("=" * 80)
            
            for p in partidos_cat:
                fecha_hora = p.fecha_hora
                hora = fecha_hora.strftime("%H:%M")
                fecha = fecha_hora.strftime("%d/%m/%Y")
                
                pareja1 = f"{p.jugador1_p1} - {p.jugador2_p1}"
                pareja2 = f"{p.jugador1_p2} - {p.jugador2_p2}"
                zona = p.zona or "Sin zona"
                cancha = p.cancha or "Sin cancha"
                
                print(f"\n🏐 Partido #{p.id_partido}")
                print(f"   📅 {fecha} a las {hora}")
                print(f"   🏟️  {cancha}")
                print(f"   📍 {zona}")
                print(f"   👥 {pareja1}")
                print(f"      vs")
                print(f"   👥 {pareja2}")

        print(f"\n{'=' * 80}")
        print(f"✅ TOTAL: {len(partidos)} partidos el sábado después de las 15:00")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    listar()
