import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("DEBUG 7MA PLAYOFFS - TORNEO 46")
print("=" * 80)

# Buscar categoría 7ma
cur.execute("""
    SELECT id_categoria, nombre FROM categorias WHERE nombre LIKE '%7ma%'
""")

categoria = cur.fetchone()
if not categoria:
    print("⚠️  No se encontró categoría 7ma")
    cur.close()
    conn.close()
    exit()

categoria_id = categoria['id_categoria']
print(f"\nCategoría: {categoria['nombre']} (ID {categoria_id})")

# Ver zonas de 7ma
print("\n" + "=" * 80)
print("ZONAS DE 7MA")
print("=" * 80)

cur.execute("""
    SELECT 
        tz.id,
        tz.nombre,
        COUNT(DISTINCT tzp.pareja_id) as parejas,
        COUNT(DISTINCT p.id_partido) as partidos
    FROM torneo_zonas tz
    LEFT JOIN torneo_zona_parejas tzp ON tz.id = tzp.zona_id
    LEFT JOIN partidos p ON tz.id = p.zona_id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = %s
    GROUP BY tz.id, tz.nombre
    ORDER BY tz.nombre
""", (categoria_id,))

zonas = cur.fetchall()

print(f"\nTotal zonas: {len(zonas)}")
for z in zonas:
    print(f"  {z['nombre']} (ID {z['id']}): {z['parejas']} parejas, {z['partidos']} partidos")

# Ver clasificados por zona
print("\n" + "=" * 80)
print("CLASIFICADOS POR ZONA")
print("=" * 80)

for zona in zonas:
    print(f"\n{zona['nombre']} (ID {zona['id']}):")
    
    # Obtener parejas de la zona con sus puntos
    cur.execute("""
        SELECT 
            tp.id,
            pu1.nombre || ' ' || pu1.apellido as j1,
            pu2.nombre || ' ' || pu2.apellido as j2,
            COALESCE(
                (SELECT SUM(CASE 
                    WHEN p.ganador_pareja_id = tp.id THEN 3
                    WHEN p.estado = 'finalizado' THEN 0
                    ELSE 0
                END)
                FROM partidos p
                WHERE (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
                AND p.zona_id = %s
                AND p.estado = 'finalizado'), 0
            ) as puntos,
            COUNT(CASE WHEN p.estado = 'finalizado' THEN 1 END) as partidos_jugados,
            COUNT(p.id_partido) as partidos_totales
        FROM torneo_zona_parejas tzp
        JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN partidos p ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id) AND p.zona_id = %s
        WHERE tzp.zona_id = %s
        GROUP BY tp.id, pu1.nombre, pu1.apellido, pu2.nombre, pu2.apellido
        ORDER BY puntos DESC, tp.id
    """, (zona['id'], zona['id'], zona['id']))
    
    parejas = cur.fetchall()
    
    for i, p in enumerate(parejas, 1):
        clasificado = "✓" if i <= 2 else "✗"
        print(f"  {clasificado} {i}º - Pareja {p['id']}: {p['j1']}/{p['j2']}")
        print(f"      {p['puntos']} pts - {p['partidos_jugados']}/{p['partidos_totales']} partidos jugados")

# Contar total de clasificados esperados
print("\n" + "=" * 80)
print("RESUMEN CLASIFICADOS")
print("=" * 80)

total_zonas = len(zonas)
clasificados_esperados = total_zonas * 2  # 2 por zona

print(f"\nTotal zonas: {total_zonas}")
print(f"Clasificados esperados: {clasificados_esperados} (2 por zona)")

# Ver si hay playoffs ya creados
cur.execute("""
    SELECT COUNT(*) as total
    FROM partidos
    WHERE id_torneo = 46
    AND categoria_id = %s
    AND fase = '8vos'
""", (categoria_id,))

playoffs_existentes = cur.fetchone()['total']

if playoffs_existentes > 0:
    print(f"\n⚠️  Ya hay {playoffs_existentes} partidos de playoffs creados")
else:
    print(f"\n✓ No hay playoffs creados aún")

# Verificar si todas las zonas tienen partidos finalizados
print("\n" + "=" * 80)
print("ESTADO DE PARTIDOS POR ZONA")
print("=" * 80)

for zona in zonas:
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN estado = 'finalizado' THEN 1 END) as finalizados
        FROM partidos
        WHERE zona_id = %s
    """, (zona['id'],))
    
    stats = cur.fetchone()
    print(f"\n{zona['nombre']}: {stats['finalizados']}/{stats['total']} partidos finalizados")
    
    if stats['finalizados'] < stats['total']:
        print(f"  ⚠️  Faltan {stats['total'] - stats['finalizados']} partidos por jugar")

cur.close()
conn.close()
