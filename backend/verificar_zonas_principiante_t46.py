import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR ZONAS PRINCIPIANTE - TORNEO 46")
print("=" * 80)

# Obtener zonas de Principiante
cur.execute("""
    SELECT 
        tz.id,
        tz.nombre,
        COUNT(tzp.pareja_id) as num_parejas
    FROM torneo_zonas tz
    LEFT JOIN torneo_zona_parejas tzp ON tzp.zona_id = tz.id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 125
    GROUP BY tz.id, tz.nombre
    ORDER BY tz.nombre
""")

zonas = cur.fetchall()

print(f"\n📊 ZONAS ENCONTRADAS: {len(zonas)}")

for z in zonas:
    print(f"\n{z['nombre']} (ID: {z['id']})")
    print(f"  - Parejas asignadas: {z['num_parejas']}")
    
    # Obtener parejas de la zona
    cur.execute("""
        SELECT 
            tp.id,
            pu1.nombre || ' ' || pu1.apellido as j1,
            pu2.nombre || ' ' || pu2.apellido as j2
        FROM torneo_zona_parejas tzp
        JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tzp.zona_id = %s
        ORDER BY tp.id
    """, (z['id'],))
    
    parejas = cur.fetchall()
    
    for p in parejas:
        print(f"    P{p['id']}: {p['j1']} / {p['j2']}")

cur.close()
conn.close()
