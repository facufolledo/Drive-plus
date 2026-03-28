import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("REVERTIR CAMBIOS DE SOLAPAMIENTOS - TORNEO 46")
print("=" * 80)

try:
    # Revertir cambio 1: Partido 1239 volver a Cancha 92
    print("\n1️⃣ Revertir Partido 1239 de Cancha 93 → Cancha 92")
    
    cur.execute("""
        UPDATE partidos
        SET cancha_id = 92
        WHERE id_partido = 1239
    """)
    
    print("   ✅ Partido 1239 vuelto a Cancha 92")
    
    # Revertir cambio 2: Partido 1166 volver a 12:30
    print("\n2️⃣ Revertir Partido 1166 de 12:40 → 12:30")
    
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 12:30:00'
        WHERE id_partido = 1166
    """)
    
    print("   ✅ Partido 1166 vuelto a 12:30")
    
    # Revertir cambio 3: Partido 1160 volver a 16:00
    print("\n3️⃣ Revertir Partido 1160 de 16:10 → 16:00")
    
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-28 16:00:00'
        WHERE id_partido = 1160
    """)
    
    print("   ✅ Partido 1160 vuelto a 16:00")
    
    conn.commit()
    
    print("\n" + "=" * 80)
    print("✅ CAMBIOS REVERTIDOS - ESTADO ORIGINAL RESTAURADO")
    print("=" * 80)

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
