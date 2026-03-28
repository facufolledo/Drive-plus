#!/usr/bin/env python3
"""
Corregir restricciones de Nicolas Lucero y Rodrigo Paez
Deben poder jugar todos los días y horarios del torneo
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

PAREJA_ID = 822

def main():
    s = Session()
    try:
        print("=" * 80)
        print("CORREGIR RESTRICCIONES - LUCERO/PAEZ")
        print("=" * 80)
        
        # Verificar restricciones actuales
        actual = s.execute(text("""
            SELECT disponibilidad_horaria
            FROM torneos_parejas
            WHERE id = :pid
        """), {"pid": PAREJA_ID}).fetchone()
        
        print(f"\n📋 Restricciones actuales:")
        if actual and actual.disponibilidad_horaria:
            print(json.dumps(actual.disponibilidad_horaria, indent=2, ensure_ascii=False))
        else:
            print("   Sin restricciones")
        
        # Nuevas restricciones: pueden jugar cualquier día y horario
        # (eliminamos las restricciones)
        print(f"\n🔄 Eliminando restricciones (pueden jugar cualquier horario)...")
        
        s.execute(text("""
            UPDATE torneos_parejas
            SET disponibilidad_horaria = NULL
            WHERE id = :pid
        """), {"pid": PAREJA_ID})
        
        s.commit()
        
        # Verificar actualización
        nueva = s.execute(text("""
            SELECT disponibilidad_horaria
            FROM torneos_parejas
            WHERE id = :pid
        """), {"pid": PAREJA_ID}).fetchone()
        
        print(f"\n✅ Restricciones actualizadas:")
        if nueva and nueva.disponibilidad_horaria:
            print(json.dumps(nueva.disponibilidad_horaria, indent=2, ensure_ascii=False))
        else:
            print("   Sin restricciones (pueden jugar cualquier horario)")
        
        print("\n" + "=" * 80)
        print("✅ ACTUALIZACIÓN COMPLETADA")
        print("=" * 80)
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
