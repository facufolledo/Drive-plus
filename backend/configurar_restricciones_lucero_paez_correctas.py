#!/usr/bin/env python3
"""
Configurar restricciones correctas para Lucero/Paez:
Pueden jugar TODOS los días del torneo, pero solo después de las 21:00
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
        print("CONFIGURAR RESTRICCIONES CORRECTAS - LUCERO/PAEZ")
        print("=" * 80)
        
        # Restricciones: jueves y viernes solo después de 21:00, sábado y domingo sin restricción
        restricciones = [
            {"dia": "jueves", "horaInicio": "21:00", "horaFin": "23:59"},
            {"dia": "viernes", "horaInicio": "21:00", "horaFin": "23:59"}
        ]
        
        print(f"\n📋 Nuevas restricciones:")
        print(json.dumps(restricciones, indent=2, ensure_ascii=False))
        print("\n✅ Pueden jugar:")
        print("   - Jueves: solo después de 21:00")
        print("   - Viernes: solo después de 21:00")
        print("   - Sábado: cualquier hora")
        print("   - Domingo: cualquier hora")
        print("\n❌ NO pueden jugar:")
        print("   - Jueves antes de 21:00")
        print("   - Viernes antes de 21:00")
        
        # Actualizar
        s.execute(text("""
            UPDATE torneos_parejas
            SET disponibilidad_horaria = CAST(:r AS jsonb)
            WHERE id = :pid
        """), {"pid": PAREJA_ID, "r": json.dumps(restricciones)})
        
        s.commit()
        
        # Verificar
        verificar = s.execute(text("""
            SELECT disponibilidad_horaria
            FROM torneos_parejas
            WHERE id = :pid
        """), {"pid": PAREJA_ID}).fetchone()
        
        print(f"\n✅ Restricciones guardadas:")
        print(json.dumps(verificar.disponibilidad_horaria, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 80)
        print("✅ CONFIGURACIÓN COMPLETADA")
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
