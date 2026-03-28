import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("ASIGNAR PAREJAS A ZONA E - TORNEO 46")
print("=" * 80)

# Obtener ID de Zona E
cur.execute("""
    SELECT id, categoria_id
    FROM torneo_zonas
    WHERE torneo_id = 46
    AND nombre = 'Zona E'
""")

zona_e = cur.fetchone()
zona_e_id = zona_e['id']
categoria_id = zona_e['categoria_id']

print(f"Zona E ID: {zona_e_id}")
print(f"Categoría ID: {categoria_id}")

# Obtener las 3 parejas de Zona E (las últimas 3 creadas)
cur.execute("""
    SELECT id
    FROM torneos_parejas
    WHERE torneo_id = 46
    AND categoria_id = %s
    ORDER BY id DESC
    LIMIT 3
""", (categoria_id,))

parejas = cur.fetchall()
parejas_ids = [p['id'] for p in parejas]

print(f"\nParejas a asignar: {parejas_ids}")

# Verificar si existe campo para zona en torneos_parejas
cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'torneos_parejas'
    AND column_name LIKE '%zona%'
""")

columnas_zona = cur.fetchall()

if columnas_zona:
    print(f"\nColumnas de zona encontradas: {[c['column_name'] for c in columnas_zona]}")
    
    # Si existe, actualizar
    for pareja_id in parejas_ids:
        cur.execute("""
            UPDATE torneos_parejas
            SET zona_id = %s
            WHERE id = %s
        """, (zona_e_id, pareja_id))
        print(f"✅ Pareja {pareja_id} asignada a Zona E")
else:
    print("\n⚠️  No hay campo zona_id en torneos_parejas")
    print("Las parejas se identifican por los partidos en la zona")

# Verificar que los partidos estén correctamente asignados
print("\n" + "=" * 80)
print("VERIFICAR PARTIDOS DE ZONA E")
print("=" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tp1.id as pareja1_id,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        tp2.id as pareja2_id,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2
    FROM partidos p
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.zona_id = %s
    ORDER BY p.fecha_hora NULLS LAST
""", (zona_e_id,))

partidos = cur.fetchall()

print(f"\nPartidos en Zona E: {len(partidos)}")

for p in partidos:
    if p['fecha_hora']:
        print(f"\n✅ Partido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')}")
    else:
        print(f"\n⚠️  Partido {p['id_partido']}: SIN HORARIO")
    print(f"   Pareja {p['pareja1_id']}: {p['j1_p1']} / {p['j2_p1']}")
    print(f"   vs")
    print(f"   Pareja {p['pareja2_id']}: {p['j1_p2']} / {p['j2_p2']}")

# Verificar parejas únicas en los partidos
parejas_en_partidos = set()
for p in partidos:
    parejas_en_partidos.add(p['pareja1_id'])
    parejas_en_partidos.add(p['pareja2_id'])

print(f"\n📊 Parejas únicas en partidos de Zona E: {sorted(parejas_en_partidos)}")

conn.commit()

print("\n" + "=" * 80)
print("✅ VERIFICACIÓN COMPLETA")
print("=" * 80)

cur.close()
conn.close()
