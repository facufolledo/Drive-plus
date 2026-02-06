"""
Script para actualizar las restricciones de la pareja #489 (Facundo Folledo / Rodrigo Saad)
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# Cargar variables de entorno
load_dotenv()

# Configurar base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no configurada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def actualizar_restricciones():
    """Actualiza las restricciones de la pareja #489"""
    db = SessionLocal()
    
    try:
        # Restricciones a agregar
        restricciones = [
            {
                "dias": ["viernes"],
                "horaInicio": "09:00",
                "horaFin": "16:00"
            },
            {
                "dias": ["viernes"],
                "horaInicio": "21:00",
                "horaFin": "23:30"
            },
            {
                "dias": ["sabado"],
                "horaInicio": "09:00",
                "horaFin": "16:00"
            }
        ]
        
        print("\n" + "="*80)
        print("ACTUALIZAR RESTRICCIONES PAREJA #489")
        print("="*80)
        
        # Verificar pareja actual
        result = db.execute(text("""
            SELECT 
                tp.id,
                u1.nombre_usuario as jugador1,
                u2.nombre_usuario as jugador2,
                tp.disponibilidad_horaria
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            WHERE tp.id = 489
        """))
        
        pareja = result.fetchone()
        
        if not pareja:
            print("\n❌ Pareja #489 no encontrada")
            return
        
        print(f"\n📋 Pareja encontrada:")
        print(f"   ID: {pareja[0]}")
        print(f"   Jugadores: {pareja[1]} / {pareja[2]}")
        print(f"   Restricciones actuales: {pareja[3]}")
        
        print(f"\n🔄 Nuevas restricciones a aplicar:")
        for idx, r in enumerate(restricciones, 1):
            print(f"   {idx}. {', '.join(r['dias'])}: {r['horaInicio']} - {r['horaFin']}")
        
        confirmacion = input("\n¿Confirmar actualización? (s/n): ")
        
        if confirmacion.lower() != 's':
            print("❌ Operación cancelada")
            return
        
        # Actualizar restricciones
        db.execute(
            text("""
                UPDATE torneos_parejas
                SET disponibilidad_horaria = :restricciones
                WHERE id = 489
            """),
            {"restricciones": json.dumps(restricciones)}
        )
        db.commit()
        
        # Verificar actualización
        result = db.execute(text("""
            SELECT disponibilidad_horaria
            FROM torneos_parejas
            WHERE id = 489
        """))
        
        nueva_disponibilidad = result.fetchone()[0]
        
        print(f"\n✅ Restricciones actualizadas exitosamente")
        print(f"\n📋 Restricciones guardadas:")
        print(json.dumps(nueva_disponibilidad, indent=2, ensure_ascii=False))
        
        print(f"\n{'='*80}")
        print("✅ ACTUALIZACIÓN COMPLETADA")
        print("="*80)
        print("\nAhora puedes:")
        print("1. Refrescar la página del torneo")
        print("2. Ver las restricciones en el modal de la pareja")
        print("3. Regenerar el fixture si es necesario")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    actualizar_restricciones()
