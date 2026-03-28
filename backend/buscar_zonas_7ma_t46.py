import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("BUSCAR ZONAS 7MA - TORNEO 46")
print("=" * 80)

# Ver todas las categorías
print("\n1️⃣  TODAS LAS CATEGORÍAS")
print("-" * 80)

cur.execute("""
    SELECT id_categoria, nombre FROM categorias ORDER BY id_categoria
""")

categorias = cur.fetchall()
for cat in categorias:
    print(f"  ID {cat['id_categoria']}: {cat['nombre']}")

# Buscar zonas de torneo 46
print("\n2️⃣  TODAS LAS ZONAS DEL TORNEO 46")
print("-" * 80)

cur.execute("""
    SELECT 
        tz.id,
        tz.nombre,
        tz.categoria_id,
        c.nombre as categoria_nombre,
        COUNT(DISTINCT tzp.pareja_id) as parejas
    FROM torneo_zonas tz
    LEFT JOIN categorias c ON tz.categoria_id = c.id_categoria
    LEFT JOIN torneo_zona_parejas tzp ON tz.id = tzp.zona_id
    WHERE tz.torneo_id = 46
    GROUP BY tz.id, tz.nombre, tz.categoria_id, c.nombre
    ORDER BY c.nombre, tz.nombre
""")

zonas = cur.fetchall()

print(f"\nTotal zonas: {len(zonas)}")

categorias_dict = {}
for z in zonas:
    cat_nombre = z['categoria_nombre'] or f"Cat {z['categoria_id']}"
    if cat_nombre not in categorias_dict:
        categorias_dict[cat_nombre] = []
    categorias_dict[cat_nombre].append(z)

for cat_nombre, zonas_cat in categorias_dict.items():
    print(f"\n{cat_nombre}:")
    for z in zonas_cat:
        print(f"  {z['nombre']} (ID {z['id']}): {z['parejas']} parejas")

# Buscar específicamente zonas con categoria_id = 2 (7ma)
print("\n3️⃣  ZONAS CON CATEGORIA_ID = 2 (7MA)")
print("-" * 80)

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
    AND tz.categoria_id = 2
    GROUP BY tz.id, tz.nombre
    ORDER BY tz.nombre
""")

zonas_7ma = cur.fetchall()

if zonas_7ma:
    print(f"\nEncontradas {len(zonas_7ma)} zonas:")
    for z in zonas_7ma:
        print(f"  {z['nombre']} (ID {z['id']}): {z['parejas']} parejas, {z['partidos']} partidos")
else:
    print("\n⚠️  No se encontraron zonas con categoria_id = 2")

# Buscar parejas de 7ma
print("\n4️⃣  PAREJAS DE 7MA EN TORNEO 46")
print("-" * 80)

cur.execute("""
    SELECT 
        tp.id,
        tp.categoria_id,
        tp.categoria_asignada,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tp.torneo_id = 46
    AND (tp.categoria_id = 2 OR tp.categoria_asignada = 2)
    ORDER BY tp.id
""")

parejas_7ma = cur.fetchall()

print(f"\nTotal parejas de 7ma: {len(parejas_7ma)}")
for p in parejas_7ma:
    print(f"  Pareja {p['id']}: {p['j1']} / {p['j2']}")
    print(f"    categoria_id: {p['categoria_id']}, categoria_asignada: {p['categoria_asignada']}")

cur.close()
conn.close()
