import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("MOVER PARTIDO 1260 - VIERNES 17:00 CANCHA 94")
print("=" * 80)

try:
    # Obtener info actual del partido
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            p.cancha_id,
            tp1.id as pareja1_id,
            pu1.nombre || ' ' || pu1.apellido as j1_p1,
            pu2.nombre || ' ' || pu2.apellido as j2_p1,
            tp2.id as pareja2_id,
            pu3.nombre || ' ' || pu3.apellido as j1_p2,
            pu4.nombre || ' ' || pu4.apellido as j2_p2
        FROM partidos p
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id_partido = 1260
    """)
    
    partido = cur.fetchone()
    
    print(f"\n📋 PARTIDO 1260")
    print(f"  P{partido['pareja1_id']}: {partido['j1_p1']} / {partido['j2_p1']}")
    print(f"  vs")
    print(f"  P{partido['pareja2_id']}: {partido['j1_p2']} / {partido['j2_p2']}")
    
    print(f"\n❌ HORARIO ACTUAL:")
    print(f"  {partido['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {partido['cancha_id']}")
    
    print(f"\n✅ NUEVO HORARIO:")
    print(f"  Friday 27/03 17:00 - Cancha 94")
    
    # Mover el partido
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 17:00:00',
            cancha_id = 94
        WHERE id_partido = 1260
    """)
    
    conn.commit()
    
    print(f"\n✅ Partido 1260 movido exitosamente")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
