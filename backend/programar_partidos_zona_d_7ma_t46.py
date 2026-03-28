import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

try:
    # Los 2 partidos nuevos de Zona D sin horario
    partidos_a_programar = [
        {
            'id': 1075,
            'fecha': '2026-03-27 20:00:00',  # Viernes 27 marzo 20:00
            'descripcion': 'Lucas Apostolo/Mariano Roldán vs Diego Bicet/Marcelo Aguilar'
        },
        {
            'id': 1076,
            'fecha': '2026-03-27 21:00:00',  # Viernes 27 marzo 21:00
            'descripcion': 'Lucas Apostolo/Mariano Roldán vs Renzo Gonzales/Erik Letterucci'
        }
    ]
    
    print("🔨 Programando partidos de Zona D:\n")
    
    for partido in partidos_a_programar:
        # Actualizar fecha_hora del partido
        cur.execute("""
            UPDATE partidos
            SET fecha_hora = %s
            WHERE id_partido = %s
        """, (partido['fecha'], partido['id']))
        
        print(f"✅ Partido {partido['id']}: {partido['descripcion']}")
        print(f"   Horario: {partido['fecha']}\n")
    
    conn.commit()
    
    # Verificar resultado
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            z.nombre as zona
        FROM partidos p
        JOIN torneo_zonas z ON p.zona_id = z.id
        WHERE p.id_torneo = 46 
        AND z.nombre = 'Zona D'
        ORDER BY p.fecha_hora
    """)
    
    print("\n📋 Partidos de Zona D programados:")
    for p in cur.fetchall():
        fecha = p['fecha_hora'].strftime('%Y-%m-%d %H:%M') if p['fecha_hora'] else 'Sin horario'
        print(f"  Partido {p['id_partido']}: {fecha}")
    
    print("\n🎉 Zona D completa con 3 partidos programados")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
