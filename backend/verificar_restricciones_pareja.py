"""
Script para verificar las restricciones de una pareja específica
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno
load_dotenv()

# Configurar base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no configurada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def verificar_restricciones():
    """Verifica las restricciones de las parejas más recientes"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*80)
        print("VERIFICAR RESTRICCIONES DE PAREJAS")
        print("="*80)
        
        # Obtener las 10 parejas más recientes
        result = db.execute(text("""
            SELECT 
                tp.id,
                tp.torneo_id,
                t.nombre as torneo_nombre,
                u1.nombre_usuario as jugador1,
                u2.nombre_usuario as jugador2,
                tp.estado,
                tp.disponibilidad_horaria,
                tp.created_at
            FROM torneos_parejas tp
            JOIN torneos t ON tp.torneo_id = t.id
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            ORDER BY tp.created_at DESC
            LIMIT 10
        """))
        
        parejas = result.fetchall()
        
        if not parejas:
            print("\n❌ No hay parejas en la base de datos")
            return
        
        print(f"\n📊 Últimas 10 parejas inscritas:\n")
        
        for pareja in parejas:
            pareja_id = pareja[0]
            torneo_id = pareja[1]
            torneo_nombre = pareja[2]
            jugador1 = pareja[3]
            jugador2 = pareja[4]
            estado = pareja[5]
            restricciones = pareja[6]
            created_at = pareja[7]
            
            print(f"{'─'*80}")
            print(f"Pareja #{pareja_id} - {jugador1} / {jugador2}")
            print(f"Torneo: {torneo_nombre} (ID: {torneo_id})")
            print(f"Estado: {estado}")
            print(f"Fecha inscripción: {created_at}")
            print(f"\nRestricciones horarias:")
            
            if restricciones is None:
                print("   ✅ Sin restricciones (puede jugar en cualquier horario)")
            elif isinstance(restricciones, list) and len(restricciones) == 0:
                print("   ✅ Array vacío (puede jugar en cualquier horario)")
            else:
                print(f"   📋 Tipo: {type(restricciones)}")
                print(f"   📋 Contenido: {restricciones}")
                
                # Intentar parsear si es lista
                if isinstance(restricciones, list):
                    print(f"\n   🔍 Detalles de restricciones:")
                    for idx, franja in enumerate(restricciones, 1):
                        if isinstance(franja, dict):
                            dias = franja.get('dias', [])
                            hora_inicio = franja.get('horaInicio', 'N/A')
                            hora_fin = franja.get('horaFin', 'N/A')
                            print(f"      Franja {idx}:")
                            print(f"         Días: {', '.join(dias)}")
                            print(f"         Horario: {hora_inicio} - {hora_fin}")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_restricciones()
