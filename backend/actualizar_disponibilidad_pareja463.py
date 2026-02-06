"""
Actualizar restricciones de Diego Bicet / Juan Cejas (pareja #463)
Pueden sábado de 10-13h y 17-23h
Restricciones: sábado 09-10h y 13-17h
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def actualizar_pareja_463():
    session = Session()
    
    try:
        # Nuevas restricciones
        restricciones = [
            {
                "dias": ["viernes"],
                "horaInicio": "09:00",
                "horaFin": "19:00"
            },
            {
                "dias": ["sabado"],
                "horaInicio": "09:00",
                "horaFin": "10:00"
            },
            {
                "dias": ["sabado"],
                "horaInicio": "13:00",
                "horaFin": "17:00"
            }
        ]
        
        print("=" * 80)
        print("ACTUALIZANDO PAREJA #463: Diego Bicet / Juan Cejas")
        print("=" * 80)
        
        # Verificar pareja actual
        pareja_actual = session.execute(
            text("""
                SELECT 
                    tp.id,
                    u1.nombre_usuario as j1,
                    u2.nombre_usuario as j2,
                    tp.disponibilidad_horaria
                FROM torneos_parejas tp
                JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
                JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
                WHERE tp.id = 463
            """)
        ).fetchone()
        
        if not pareja_actual:
            print("❌ Pareja #463 no encontrada")
            return
        
        print(f"\n📋 Pareja actual:")
        print(f"   ID: {pareja_actual[0]}")
        print(f"   Jugadores: {pareja_actual[1]} / {pareja_actual[2]}")
        print(f"\n   Restricciones actuales:")
        if pareja_actual[3]:
            for r in pareja_actual[3]:
                dias = ", ".join(r['dias'])
                print(f"      • {dias}: {r['horaInicio']} - {r['horaFin']}")
        else:
            print("      Sin restricciones")
        
        # Actualizar
        session.execute(
            text("""
                UPDATE torneos_parejas
                SET disponibilidad_horaria = :restricciones
                WHERE id = 463
            """),
            {"restricciones": json.dumps(restricciones)}
        )
        
        session.commit()
        
        print(f"\n✅ Restricciones actualizadas:")
        for r in restricciones:
            dias = ", ".join(r['dias'])
            print(f"   • {dias}: NO pueden de {r['horaInicio']} a {r['horaFin']}")
        
        print(f"\n{'=' * 80}")
        print("✅ Actualización completada")
        print("=" * 80)
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    actualizar_pareja_463()
