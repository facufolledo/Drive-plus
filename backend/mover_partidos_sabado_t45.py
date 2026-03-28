#!/usr/bin/env python3
"""
Mover partidos del sábado a jueves y viernes después de las 22:00 - Torneo 45
Partidos a mover: 745, 761, 762, 763
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

# Partidos a mover y sus nuevos horarios
# Jueves 22:10 ya ocupado en Cancha 1, 2, 3
# Viernes 22:10 ya ocupado en Cancha 1, 2, 3
# Usar 23:00
# IDs de canchas: 89=Cancha 1, 90=Cancha 2, 91=Cancha 3
MOVIMIENTOS = [
    # Partido 745: 6ta Zona F - Salazar/Charazo vs Santillan/Paredes
    {"partido_id": 745, "nueva_fecha": "2026-03-06 23:00:00", "cancha_id": 89},  # Viernes 23:00 Cancha 1
    
    # Partido 761: 8va Zona D - Colina/Colina vs Toledo/Tramontin
    {"partido_id": 761, "nueva_fecha": "2026-03-05 23:00:00", "cancha_id": 89},  # Jueves 23:00 Cancha 1
    
    # Partido 762: 8va Zona D - Colina/Colina vs Gonzalez/Imanol
    {"partido_id": 762, "nueva_fecha": "2026-03-05 23:00:00", "cancha_id": 90},  # Jueves 23:00 Cancha 2
    
    # Partido 763: 8va Zona D - Toledo/Tramontin vs Gonzalez/Imanol
    {"partido_id": 763, "nueva_fecha": "2026-03-06 23:00:00", "cancha_id": 90},  # Viernes 23:00 Cancha 2
]

def mover():
    s = Session()
    try:
        print("=" * 80)
        print(f"MOVER PARTIDOS DEL SÁBADO - TORNEO {TORNEO_ID}")
        print("=" * 80)

        for mov in MOVIMIENTOS:
            partido_id = mov["partido_id"]
            nueva_fecha = datetime.strptime(mov["nueva_fecha"], "%Y-%m-%d %H:%M:%S")
            cancha_id = mov["cancha_id"]
            
            # Obtener info del partido
            partido = s.execute(text("""
                SELECT 
                    p.fecha_hora,
                    tc.nombre as categoria,
                    tz.nombre as zona,
                    tca.nombre as cancha_actual
                FROM partidos p
                JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                LEFT JOIN torneo_categorias tc ON tp1.categoria_id = tc.id
                LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
                LEFT JOIN torneo_canchas tca ON p.cancha_id = tca.id
                WHERE p.id_partido = :pid
            """), {"pid": partido_id}).fetchone()
            
            if not partido:
                print(f"\n❌ Partido {partido_id} no encontrado")
                continue
            
            # Obtener nombre de nueva cancha
            cancha_nueva = s.execute(text("""
                SELECT nombre FROM torneo_canchas WHERE id = :cid
            """), {"cid": cancha_id}).fetchone()
            
            fecha_actual = partido.fecha_hora
            categoria = partido.categoria or "?"
            zona = partido.zona or "?"
            cancha_actual = partido.cancha_actual or "?"
            cancha_nueva_nombre = cancha_nueva[0] if cancha_nueva else f"Cancha {cancha_id}"
            
            print(f"\n🏐 Partido #{partido_id} - {categoria} {zona}")
            print(f"   📅 Actual: {fecha_actual.strftime('%d/%m/%Y %H:%M')} - {cancha_actual}")
            print(f"   ➡️  Nueva:  {nueva_fecha.strftime('%d/%m/%Y %H:%M')} - {cancha_nueva_nombre}")
            
            # Actualizar
            s.execute(text("""
                UPDATE partidos
                SET fecha_hora = :fh, cancha_id = :cid
                WHERE id_partido = :pid
            """), {"fh": nueva_fecha, "cid": cancha_id, "pid": partido_id})
            
            print(f"   ✅ Movido")

        s.commit()

        print(f"\n{'=' * 80}")
        print(f"✅ LISTO - {len(MOVIMIENTOS)} partidos movidos")
        print("=" * 80)

    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    mover()
