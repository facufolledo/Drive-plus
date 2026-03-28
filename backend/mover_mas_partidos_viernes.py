import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

try:
    print("🔨 Moviendo partidos 1208 y 1195 al viernes:\n")
    
    # Partido 1208: de sábado 21:00 a viernes 23:00
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 23:00:00'
        WHERE id_partido = 1208
        RETURNING id_partido, fecha_hora
    """)
    
    partido = cur.fetchone()
    if partido:
        print(f"✅ Partido {partido['id_partido']}: Movido a {partido['fecha_hora']}")
    else:
        print(f"❌ Partido 1208 no encontrado")
    
    # Partido 1195: de sábado 19:00 a viernes 19:00
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 19:00:00'
        WHERE id_partido = 1195
        RETURNING id_partido, fecha_hora
    """)
    
    partido = cur.fetchone()
    if partido:
        print(f"✅ Partido {partido['id_partido']}: Movido a {partido['fecha_hora']}")
    else:
        print(f"❌ Partido 1195 no encontrado")
    
    conn.commit()
    
    # Verificar distribución final por día
    cur.execute("""
        SELECT 
            CASE 
                WHEN EXTRACT(DAY FROM fecha_hora) = 27 THEN 'Viernes'
                WHEN EXTRACT(DAY FROM fecha_hora) = 28 THEN 'Sábado'
                ELSE 'Otro'
            END as dia,
            COUNT(*) as total
        FROM partidos
        WHERE id_torneo = 46 
        AND categoria_id = (SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '7ma')
        GROUP BY dia
        ORDER BY dia
    """)
    
    print("\n📊 Distribución de partidos por día:")
    for row in cur.fetchall():
        print(f"  {row['dia']}: {row['total']} partidos")
    
    print("\n🎉 Partidos movidos correctamente")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
