import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

try:
    # Obtener IDs
    cur.execute("SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '7ma'")
    categoria_id = cur.fetchone()['id']
    
    cur.execute("SELECT id FROM torneo_zonas WHERE torneo_id = 46 AND categoria_id = %s AND nombre = 'Zona D'", (categoria_id,))
    zona_d_id = cur.fetchone()['id']
    
    print(f"Categoría 7ma: ID {categoria_id}")
    print(f"Zona D: ID {zona_d_id}\n")
    
    # Los 2 partidos faltantes de Zona D con la pareja 1005
    partidos_nuevos = [
        {'pareja1': 1005, 'pareja2': 1016, 'fecha': '2026-03-28 20:00:00', 'desc': 'Lucas Apostolo/Mariano Roldán vs Diego Bicet/Marcelo Aguilar'},
        {'pareja1': 1005, 'pareja2': 1023, 'fecha': '2026-03-28 21:00:00', 'desc': 'Lucas Apostolo/Mariano Roldán vs Renzo Gonzales/Erik Letterucci'},
    ]
    
    print("🔨 Agregando partidos faltantes de Zona D:\n")
    
    for partido in partidos_nuevos:
        cur.execute("""
            INSERT INTO partidos (
                id_torneo, categoria_id, zona_id,
                pareja1_id, pareja2_id,
                fase, estado, fecha, fecha_hora, id_creador
            ) VALUES (
                %s, %s, %s,
                %s, %s,
                'zona', 'pendiente', NOW(), %s, 1
            )
            RETURNING id_partido
        """, (46, categoria_id, zona_d_id, partido['pareja1'], partido['pareja2'], partido['fecha']))
        
        partido_id = cur.fetchone()['id_partido']
        print(f"✅ Partido {partido_id}: {partido['desc']} - {partido['fecha']}")
    
    conn.commit()
    
    # Verificar total de partidos en Zona D
    cur.execute("""
        SELECT COUNT(*) as total
        FROM partidos
        WHERE id_torneo = 46 AND categoria_id = %s AND zona_id = %s
    """, (categoria_id, zona_d_id))
    
    total = cur.fetchone()['total']
    
    print(f"\n🎉 Zona D completada con {total} partidos (3 parejas, todos contra todos)")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
