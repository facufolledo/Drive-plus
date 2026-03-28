import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

try:
    print("🔨 Moviendo partidos de Zona D al viernes:\n")
    
    # Partido 1194: de sábado 19:00 a viernes 21:00
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 21:00:00'
        WHERE id_partido = 1194
        RETURNING id_partido, fecha_hora
    """)
    
    partido = cur.fetchone()
    if partido:
        print(f"✅ Partido {partido['id_partido']}: Movido a {partido['fecha_hora']}")
    
    # Partido 1207: de sábado 20:00 a viernes 22:00
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 22:00:00'
        WHERE id_partido = 1207
        RETURNING id_partido, fecha_hora
    """)
    
    partido = cur.fetchone()
    if partido:
        print(f"✅ Partido {partido['id_partido']}: Movido a {partido['fecha_hora']}")
    
    conn.commit()
    
    # Verificar todos los partidos de Zona D
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            tp1.id as p1_id,
            tp2.id as p2_id
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        WHERE p.id_torneo = 46 
        AND z.nombre = 'Zona D'
        ORDER BY p.fecha_hora
    """)
    
    print("\n📋 Partidos de Zona D actualizados:")
    for p in cur.fetchall():
        fecha = p['fecha_hora'].strftime('%Y-%m-%d %H:%M')
        dia = 'Viernes' if '27' in fecha else 'Sábado'
        print(f"  Partido {p['id_partido']}: P{p['p1_id']} vs P{p['p2_id']} - {dia} {fecha}")
    
    print("\n🎉 Partidos movidos al viernes correctamente")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
