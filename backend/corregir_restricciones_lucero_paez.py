#!/usr/bin/env python3
"""
Corregir restricciones de Lucero-Paez en 6ta del torneo 45.
NO pueden después de las 21:00 jueves y viernes.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def corregir():
    s = Session()
    try:
        print("=" * 70)
        print(f"CORREGIR RESTRICCIONES LUCERO-PAEZ - TORNEO {TORNEO_ID}")
        print("=" * 70)

        # Buscar la pareja
        pareja = s.execute(text("""
            SELECT tp.id, u1.nombre_usuario, u2.nombre_usuario, tp.disponibilidad_horaria
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            WHERE tp.torneo_id = :t
            AND (u1.nombre_usuario LIKE '%lucero%' OR u2.nombre_usuario LIKE '%lucero%')
            AND (u1.nombre_usuario LIKE '%paez%' OR u2.nombre_usuario LIKE '%paez%')
        """), {"t": TORNEO_ID}).fetchone()

        if not pareja:
            print("\n❌ Pareja Lucero-Paez no encontrada")
            return

        pareja_id = pareja[0]
        print(f"\n✅ Pareja encontrada:")
        print(f"   ID: {pareja_id}")
        print(f"   Jugadores: {pareja[1]} - {pareja[2]}")
        print(f"   Restricciones actuales: {pareja[3]}")

        # Nuevas restricciones: NO pueden después de 21:00 jueves y viernes
        restricciones = [
            {"dia": "jueves", "horaInicio": "21:00", "horaFin": "23:59"},
            {"dia": "viernes", "horaInicio": "21:00", "horaFin": "23:59"}
        ]

        print(f"\n🔄 Actualizando restricciones...")
        s.execute(text("""
            UPDATE torneos_parejas
            SET disponibilidad_horaria = :disp
            WHERE id = :pid
        """), {"disp": json.dumps(restricciones), "pid": pareja_id})

        s.commit()

        print(f"   ✅ Restricciones actualizadas")
        print(f"   📋 NO pueden después de 21:00 jueves y viernes")
        print(f"\n{'=' * 70}")
        print(f"✅ LISTO")
        print("=" * 70)

    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    corregir()
