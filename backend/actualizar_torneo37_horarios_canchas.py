"""
Script para actualizar horarios y canchas del torneo 37
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

def actualizar_torneo37():
    """Actualiza horarios y canchas del torneo 37"""
    session = Session()
    
    try:
        print("=" * 80)
        print("ACTUALIZAR TORNEO 37 - HORARIOS Y CANCHAS")
        print("=" * 80)
        
        # Verificar que el torneo existe
        torneo = session.execute(
            text("SELECT id, nombre FROM torneos WHERE id = 37")
        ).fetchone()
        
        if not torneo:
            print("❌ El torneo 37 no existe")
            return
        
        print(f"\n✅ Torneo: {torneo[1]}")
        
        # Configurar horarios
        # Viernes 15:00-23:30, Sábado y Domingo 09:00-23:30
        horarios = [
            {
                "dias": ["viernes"],
                "horaInicio": "15:00",
                "horaFin": "23:30"
            },
            {
                "dias": ["sabado"],
                "horaInicio": "09:00",
                "horaFin": "23:30"
            },
            {
                "dias": ["domingo"],
                "horaInicio": "09:00",
                "horaFin": "23:30"
            }
        ]
        
        print(f"\n⏰ HORARIOS A CONFIGURAR:")
        for h in horarios:
            dias = ", ".join(h['dias'])
            print(f"   • {dias}: {h['horaInicio']} - {h['horaFin']}")
        
        # Actualizar horarios
        horarios_json = json.dumps(horarios)
        session.execute(
            text("""
                UPDATE torneos 
                SET horarios_disponibles = CAST(:horarios AS jsonb)
                WHERE id = 37
            """),
            {"horarios": horarios_json}
        )
        print(f"\n✅ Horarios actualizados")
        
        # Verificar si ya existen canchas
        canchas_existentes = session.execute(
            text("SELECT COUNT(*) FROM torneo_canchas WHERE torneo_id = 37")
        ).fetchone()[0]
        
        if canchas_existentes > 0:
            print(f"\n⚠️  Ya existen {canchas_existentes} cancha(s). Eliminando...")
            session.execute(
                text("DELETE FROM torneo_canchas WHERE torneo_id = 37")
            )
        
        # Crear 5 canchas
        print(f"\n🏟️  CREANDO 5 CANCHAS:")
        for i in range(1, 6):
            session.execute(
                text("""
                    INSERT INTO torneo_canchas (torneo_id, nombre, activa)
                    VALUES (37, :nombre, true)
                """),
                {"nombre": f"Cancha {i}"}
            )
            print(f"   ✅ Cancha {i}")
        
        session.commit()
        
        print(f"\n{'=' * 80}")
        print("✅ TORNEO 37 ACTUALIZADO CORRECTAMENTE")
        print(f"{'=' * 80}")
        print(f"\n📋 Resumen:")
        print(f"   • 3 franjas horarias configuradas")
        print(f"   • 5 canchas creadas")
        print(f"\n🎾 El torneo está listo para generar zonas y fixture")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    actualizar_torneo37()
