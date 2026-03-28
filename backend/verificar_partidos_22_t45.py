#!/usr/bin/env python3
"""
Verificar partidos a las 22:00 jueves y viernes - Torneo 45
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def verificar():
    s = Session()
    try:
        print("=" * 80)
        print(f"PARTIDOS A LAS 22:00 JUEVES Y VIERNES - TORNEO {TORNEO_ID}")
        print("=" * 80)

        # Obtener partidos jueves y viernes a las 22:00
        partidos = s.execute(text("""
            SELECT 
                p.id_partido,
                p.fecha_hora,
                tc.nombre as categoria,
                tz.nombre as zona,
                tca.nombre as cancha,
                EXTRACT(DOW FROM p.fecha_hora) as dia_semana,
                EXTRACT(HOUR FROM p.fecha_hora) as hora
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            LEFT JOIN torneo_categorias tc ON tp1.categoria_id = tc.id
            LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
            LEFT JOIN torneo_canchas tca ON p.cancha_id = tca.id
            WHERE tp1.torneo_id = :t
            AND EXTRACT(DOW FROM p.fecha_hora) IN (4, 5)
            AND EXTRACT(HOUR FROM p.fecha_hora) >= 22
            ORDER BY p.fecha_hora, tca.nombre
        """), {"t": TORNEO_ID}).fetchall()

        if not partidos:
            print("\n✅ No hay partidos a las 22:00 o después en jueves y viernes")
            return

        print(f"\n📋 Total: {len(partidos)} partidos\n")

        dia_nombres = {4: "Jueves", 5: "Viernes"}
        
        for p in partidos:
            dia = dia_nombres.get(p.dia_semana, "?")
            fecha_hora = p.fecha_hora.strftime("%d/%m/%Y %H:%M")
            categoria = p.categoria or "?"
            zona = p.zona or "?"
            cancha = p.cancha or "?"
            
            print(f"🏐 Partido #{p.id_partido}")
            print(f"   📅 {dia} {fecha_hora}")
            print(f"   🏟️  {cancha}")
            print(f"   📍 {categoria} - {zona}")
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
