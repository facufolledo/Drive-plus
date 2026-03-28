import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR FIXTURE PRINCIPIANTE - TORNEO 46")
print("=" * 80)

# Obtener categoría Principiante
cur.execute("""
    SELECT id FROM torneo_categorias
    WHERE torneo_id = 46 AND nombre = 'Principiante'
""")

categoria = cur.fetchone()
if not categoria:
    print("❌ Categoría Principiante no encontrada")
    cur.close()
    conn.close()
    exit(1)

categoria_id = categoria['id']

# Obtener partidos generados
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tz.nombre as zona,
        tp1.id as pareja1_id,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        tp2.id as pareja2_id,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46
    AND p.categoria_id = %s
    AND p.fase = 'zona'
    ORDER BY tz.nombre, p.fecha_hora
""", (categoria_id,))

partidos = cur.fetchall()

print(f"\n📊 PARTIDOS GENERADOS: {len(partidos)}")

if not partidos:
    print("⚠️  No se encontraron partidos")
else:
    zona_actual = None
    for p in partidos:
        if p['zona'] != zona_actual:
            zona_actual = p['zona']
            print(f"\n{'=' * 80}")
            print(f"{zona_actual}")
            print(f"{'=' * 80}")
        
        fecha_hora = p['fecha_hora'].strftime('%A %d/%m %H:%M') if p['fecha_hora'] else 'SIN PROGRAMAR'
        cancha = f"Cancha {p['cancha_id']}" if p['cancha_id'] else 'Sin cancha'
        
        print(f"\nPartido {p['id_partido']}: {fecha_hora} - {cancha}")
        print(f"  P{p['pareja1_id']}: {p['j1_p1']} / {p['j2_p1']}")
        print(f"  vs")
        print(f"  P{p['pareja2_id']}: {p['j1_p2']} / {p['j2_p2']}")

# Verificar zonas
cur.execute("""
    SELECT 
        tz.id,
        tz.nombre,
        COUNT(DISTINCT p.id_partido) as num_partidos,
        COUNT(DISTINCT CASE WHEN p.fecha_hora IS NOT NULL THEN p.id_partido END) as partidos_programados
    FROM torneo_zonas tz
    LEFT JOIN partidos p ON p.zona_id = tz.id AND p.fase = 'zona'
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = %s
    GROUP BY tz.id, tz.nombre
    ORDER BY tz.nombre
""", (categoria_id,))

zonas = cur.fetchall()

print(f"\n{'=' * 80}")
print("RESUMEN POR ZONA")
print(f"{'=' * 80}")

for z in zonas:
    print(f"\n{z['nombre']} (ID: {z['id']})")
    print(f"  - Partidos totales: {z['num_partidos']}")
    print(f"  - Partidos programados: {z['partidos_programados']}")
    if z['num_partidos'] != z['partidos_programados']:
        print(f"  ⚠️  {z['num_partidos'] - z['partidos_programados']} partidos sin programar")

cur.close()
conn.close()
