#!/usr/bin/env python3
"""
Actualizar horarios del torneo 45: jueves y viernes empiezan a las 14:00.
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

def actualizar():
    s = Session()
    try:
        print("=" * 70)
        print(f"ACTUALIZAR HORARIOS - TORNEO {TORNEO_ID}")
        print("=" * 70)

        # Verificar torneo
        torneo = s.execute(text("SELECT id, nombre FROM torneos WHERE id = :t"), {"t": TORNEO_ID}).fetchone()
        if not torneo:
            print(f"\n❌ Torneo {TORNEO_ID} no encontrado")
            return
        
        print(f"✅ Torneo: {torneo.nombre}")

        # Obtener horarios actuales de jueves y viernes
        print(f"\n📋 Horarios actuales:")
        horarios = s.execute(text("""
            SELECT id, dia_semana, hora_inicio, hora_fin 
            FROM torneo_horarios 
            WHERE torneo_id = :t AND dia_semana IN ('jueves', 'viernes')
            ORDER BY dia_semana, hora_inicio
        """), {"t": TORNEO_ID}).fetchall()
        
        for h in horarios:
            print(f"   {h.dia_semana}: {h.hora_inicio} - {h.hora_fin}")

        # Actualizar jueves: cambiar 15:00 por 14:00
        print(f"\n🔄 Actualizando horarios...")
        
        jueves_updated = s.execute(text("""
            UPDATE torneo_horarios 
            SET hora_inicio = '14:00:00'
            WHERE torneo_id = :t 
            AND dia_semana = 'jueves' 
            AND hora_inicio = '15:00:00'
        """), {"t": TORNEO_ID})
        
        viernes_updated = s.execute(text("""
            UPDATE torneo_horarios 
            SET hora_inicio = '14:00:00'
            WHERE torneo_id = :t 
            AND dia_semana = 'viernes' 
            AND hora_inicio = '15:00:00'
        """), {"t": TORNEO_ID})
        
        s.commit()
        
        print(f"   ✅ Jueves: {jueves_updated.rowcount} horarios actualizados")
        print(f"   ✅ Viernes: {viernes_updated.rowcount} horarios actualizados")

        # Mostrar horarios actualizados
        print(f"\n📋 Horarios nuevos:")
        horarios_nuevos = s.execute(text("""
            SELECT id, dia_semana, hora_inicio, hora_fin 
            FROM torneo_horarios 
            WHERE torneo_id = :t AND dia_semana IN ('jueves', 'viernes')
            ORDER BY dia_semana, hora_inicio
        """), {"t": TORNEO_ID}).fetchall()
        
        for h in horarios_nuevos:
            print(f"   {h.dia_semana}: {h.hora_inicio} - {h.hora_fin}")

        print(f"\n{'=' * 70}")
        print(f"✅ LISTO - Horarios actualizados")
        print("=" * 70)

    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    actualizar()
