import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("COMPARAR ZONA E CON OTRAS ZONAS - TORNEO 46")
print("=" * 80)

# Comparar con Zona A de Principiante (que sí funciona)
print("\n🔹 ZONA A - PRINCIPIANTE (REFERENCIA)")
print("-" * 80)

cur.execute("""
    SELECT 
        tz.id as zona_id,
        tz.nombre as zona_nombre,
        tp.id as pareja_id,
        tp.torneo_id,
        tp.categoria_id,
        tp.categoria_asignada,
        tp.estado,
        tp.pago_estado,
        tp.confirmado_jugador1,
        tp.confirmado_jugador2,
        tp.created_at,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneo_zonas tz
    JOIN torneos_parejas tp ON tp.categoria_id = tz.categoria_id AND tp.torneo_id = tz.torneo_id
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 125
    AND tz.nombre = 'Zona A'
    AND tp.id IN (
        SELECT DISTINCT pareja1_id FROM partidos WHERE zona_id = tz.id
        UNION
        SELECT DISTINCT pareja2_id FROM partidos WHERE zona_id = tz.id
    )
    ORDER BY tp.id
    LIMIT 2
""")

zona_a = cur.fetchall()

if zona_a:
    for p in zona_a:
        print(f"\nPareja {p['pareja_id']}: {p['j1']} / {p['j2']}")
        print(f"  torneo_id: {p['torneo_id']}")
        print(f"  categoria_id: {p['categoria_id']}")
        print(f"  categoria_asignada: {p['categoria_asignada']}")
        print(f"  estado: {p['estado']}")
        print(f"  pago_estado: {p['pago_estado']}")
        print(f"  confirmado_j1: {p['confirmado_jugador1']}")
        print(f"  confirmado_j2: {p['confirmado_jugador2']}")
        print(f"  created_at: {p['created_at']}")
else:
    print("  ⚠️  No se encontraron parejas en Zona A")

# Ahora Zona E
print("\n" + "=" * 80)
print("🔹 ZONA E - PRINCIPIANTE (PROBLEMA)")
print("-" * 80)

cur.execute("""
    SELECT 
        tz.id as zona_id,
        tz.nombre as zona_nombre,
        tp.id as pareja_id,
        tp.torneo_id,
        tp.categoria_id,
        tp.categoria_asignada,
        tp.estado,
        tp.pago_estado,
        tp.confirmado_jugador1,
        tp.confirmado_jugador2,
        tp.created_at,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneo_zonas tz
    JOIN partidos p ON p.zona_id = tz.id
    JOIN torneos_parejas tp ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tz.torneo_id = 46
    AND tz.id = 426
    GROUP BY tz.id, tz.nombre, tp.id, tp.torneo_id, tp.categoria_id, tp.categoria_asignada, 
             tp.estado, tp.pago_estado, tp.confirmado_jugador1, tp.confirmado_jugador2, 
             tp.created_at, pu1.nombre, pu1.apellido, pu2.nombre, pu2.apellido
    ORDER BY tp.id
""")

zona_e = cur.fetchall()

for p in zona_e:
    print(f"\nPareja {p['pareja_id']}: {p['j1']} / {p['j2']}")
    print(f"  torneo_id: {p['torneo_id']}")
    print(f"  categoria_id: {p['categoria_id']}")
    print(f"  categoria_asignada: {p['categoria_asignada']}")
    print(f"  estado: {p['estado']}")
    print(f"  pago_estado: {p['pago_estado']}")
    print(f"  confirmado_j1: {p['confirmado_jugador1']}")
    print(f"  confirmado_j2: {p['confirmado_jugador2']}")
    print(f"  created_at: {p['created_at']}")

# Comparar partidos
print("\n" + "=" * 80)
print("COMPARAR PARTIDOS")
print("=" * 80)

print("\n🔹 PARTIDO DE ZONA A (REFERENCIA)")
print("-" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.torneo_id,
        p.categoria_id,
        p.zona_id,
        p.pareja1_id,
        p.pareja2_id,
        p.fecha,
        p.fecha_hora,
        p.cancha_id,
        p.estado,
        p.id_creador,
        p.created_at
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 125
    AND tz.nombre = 'Zona A'
    LIMIT 1
""")

partido_a = cur.fetchone()

if partido_a:
    print(f"\nPartido {partido_a['id_partido']}:")
    print(f"  torneo_id: {partido_a['torneo_id']}")
    print(f"  categoria_id: {partido_a['categoria_id']}")
    print(f"  zona_id: {partido_a['zona_id']}")
    print(f"  pareja1_id: {partido_a['pareja1_id']}")
    print(f"  pareja2_id: {partido_a['pareja2_id']}")
    print(f"  fecha: {partido_a['fecha']}")
    print(f"  fecha_hora: {partido_a['fecha_hora']}")
    print(f"  cancha_id: {partido_a['cancha_id']}")
    print(f"  estado: {partido_a['estado']}")
    print(f"  id_creador: {partido_a['id_creador']}")
    print(f"  created_at: {partido_a['created_at']}")

print("\n🔹 PARTIDOS DE ZONA E")
print("-" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.torneo_id,
        p.categoria_id,
        p.zona_id,
        p.pareja1_id,
        p.pareja2_id,
        p.fecha,
        p.fecha_hora,
        p.cancha_id,
        p.estado,
        p.id_creador,
        p.created_at
    FROM partidos p
    WHERE p.zona_id = 426
    ORDER BY p.id_partido
""")

partidos_e = cur.fetchall()

for p in partidos_e:
    print(f"\nPartido {p['id_partido']}:")
    print(f"  torneo_id: {p['torneo_id']}")
    print(f"  categoria_id: {p['categoria_id']}")
    print(f"  zona_id: {p['zona_id']}")
    print(f"  pareja1_id: {p['pareja1_id']}")
    print(f"  pareja2_id: {p['pareja2_id']}")
    print(f"  fecha: {p['fecha']}")
    print(f"  fecha_hora: {p['fecha_hora']}")
    print(f"  cancha_id: {p['cancha_id']}")
    print(f"  estado: {p['estado']}")
    print(f"  id_creador: {p['id_creador']}")
    print(f"  created_at: {p['created_at']}")

# Verificar si las parejas están en torneo_zona_parejas
print("\n" + "=" * 80)
print("VERIFICAR TABLA torneo_zona_parejas")
print("=" * 80)

print("\n🔹 ZONA A - Parejas en torneo_zona_parejas")
cur.execute("""
    SELECT tzp.*, tz.nombre as zona_nombre
    FROM torneo_zona_parejas tzp
    JOIN torneo_zonas tz ON tzp.zona_id = tz.id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 125
    AND tz.nombre = 'Zona A'
    LIMIT 2
""")

zona_a_parejas = cur.fetchall()
print(f"  Parejas encontradas: {len(zona_a_parejas)}")
for p in zona_a_parejas:
    print(f"    Pareja {p['pareja_id']} en Zona {p['zona_id']}")

print("\n🔹 ZONA E - Parejas en torneo_zona_parejas")
cur.execute("""
    SELECT tzp.*
    FROM torneo_zona_parejas tzp
    WHERE tzp.zona_id = 426
""")

zona_e_parejas = cur.fetchall()
print(f"  Parejas encontradas: {len(zona_e_parejas)}")
if zona_e_parejas:
    for p in zona_e_parejas:
        print(f"    Pareja {p['pareja_id']} en Zona {p['zona_id']}")
else:
    print("  ⚠️  NO HAY PAREJAS EN torneo_zona_parejas PARA ZONA E")
    print("\n  🔧 ESTO ES EL PROBLEMA - Necesitamos insertar en torneo_zona_parejas")

cur.close()
conn.close()
