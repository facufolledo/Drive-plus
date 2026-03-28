import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import json

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CORREGIR RESTRICCIÓN PAREJA 1041 - BENJAMÍN JATUFF / MANUEL ALCAZAR")
print("=" * 80)

try:
    # Ver restricción actual
    cur.execute("""
        SELECT 
            tp.id,
            tp.disponibilidad_horaria,
            pu1.nombre || ' ' || pu1.apellido as j1,
            pu2.nombre || ' ' || pu2.apellido as j2
        FROM torneos_parejas tp
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id = 1041
    """)
    
    pareja = cur.fetchone()
    
    print(f"\n📋 PAREJA: {pareja['j1']} / {pareja['j2']}")
    print(f"\n❌ RESTRICCIÓN ACTUAL (INCORRECTA):")
    for r in pareja['disponibilidad_horaria']:
        dias = ', '.join(r['dias'])
        print(f"   - NO disponible {dias} de {r['horaInicio']} a {r['horaFin']}")
    
    # Nueva restricción corregida
    nueva_restriccion = [
        {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '16:59'},
        {'dias': ['viernes'], 'horaInicio': '17:30', 'horaFin': '23:59'}  # Cambiado de 17:01 a 17:30
    ]
    
    print(f"\n✅ NUEVA RESTRICCIÓN (CORREGIDA):")
    for r in nueva_restriccion:
        dias = ', '.join(r['dias'])
        print(f"   - NO disponible {dias} de {r['horaInicio']} a {r['horaFin']}")
    
    print(f"\n   ⏰ HORARIO DISPONIBLE: Viernes 17:00 - 17:29, Sábado libre")
    
    # Actualizar
    cur.execute("""
        UPDATE torneos_parejas
        SET disponibilidad_horaria = %s::jsonb
        WHERE id = 1041
    """, (json.dumps(nueva_restriccion),))
    
    conn.commit()
    
    print(f"\n✅ Restricción actualizada correctamente")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
