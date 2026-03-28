#!/usr/bin/env python3
"""
Verificar partidos 791 y 755 específicamente
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

def main():
    s = Session()
    try:
        print("=" * 80)
        print("VERIFICAR PARTIDOS 791 Y 755")
        print("=" * 80)

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
            WHERE p.id_partido IN (791, 755)
            ORDER BY p.id_partido
        """)).fetchall()

        for p in partidos:
            print(f"\n🏐 Partido #{p.id_partido}")
            print(f"📅 Fecha/Hora UTC: {p.fecha_hora}")
            print(f"📅 Fecha/Hora Local (UTC-3): {p.fecha_hora - timedelta(hours=3)}")
            print(f"🏟️  Cancha: {p.cancha} (ID: {p.cancha_id})")
            print(f"📍 {p.categoria} - {p.zona}")
            print(f"👥 {p.j1_p1} - {p.j2_p1} vs {p.j1_p2} - {p.j2_p2}")
            
            # Calcular fin del partido
            fin_utc = p.fecha_hora + timedelta(minutes=50)
            fin_local = fin_utc - timedelta(hours=3)
            print(f"⏱️  Fin estimado UTC: {fin_utc}")
            print(f"⏱️  Fin estimado Local: {fin_local}")

        # Verificar solapamiento
        if len(partidos) == 2:
            p1, p2 = partidos[0], partidos[1]
            fin_p1 = p1.fecha_hora + timedelta(minutes=50)
            
            print("\n" + "=" * 80)
            print("ANÁLISIS DE SOLAPAMIENTO")
            print("=" * 80)
            
            print(f"\nPartido {p1.id_partido}:")
            print(f"  Inicio: {p1.fecha_hora} UTC ({(p1.fecha_hora - timedelta(hours=3)).strftime('%H:%M')} local)")
            print(f"  Fin:    {fin_p1} UTC ({(fin_p1 - timedelta(hours=3)).strftime('%H:%M')} local)")
            print(f"  Cancha: {p1.cancha_id}")
            
            print(f"\nPartido {p2.id_partido}:")
            print(f"  Inicio: {p2.fecha_hora} UTC ({(p2.fecha_hora - timedelta(hours=3)).strftime('%H:%M')} local)")
            print(f"  Cancha: {p2.cancha_id}")
            
            # Verificar si se solapan
            if p1.cancha_id == p2.cancha_id:
                if p2.fecha_hora < fin_p1:
                    diferencia = (p2.fecha_hora - p1.fecha_hora).total_seconds() / 60
                    print(f"\n🚨 SOLAPAMIENTO DETECTADO!")
                    print(f"   Misma cancha ({p1.cancha})")
                    print(f"   Diferencia entre inicios: {diferencia:.0f} minutos")
                    print(f"   Duración partido: 50 minutos")
                    print(f"   Solapamiento: {50 - diferencia:.0f} minutos")
                else:
                    print(f"\n✅ NO HAY SOLAPAMIENTO")
            else:
                print(f"\n✅ Canchas diferentes, no hay conflicto")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
