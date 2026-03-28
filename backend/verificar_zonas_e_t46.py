import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR ZONAS E - TORNEO 46")
print("=" * 80)

# Buscar todas las zonas E
cur.execute("""
    SELECT 
        tz.id,
        tz.nombre,
        tz.categoria_id,
        tc.nombre as categoria_nombre,
        tz.created_at
    FROM torneo_zonas tz
    JOIN torneo_categorias tc ON tz.categoria_id = tc.id
    WHERE tz.torneo_id = 46
    AND tz.nombre = 'Zona E'
    ORDER BY tz.id
""")

zonas_e = cur.fetchall()

print(f"\n📊 Zonas E encontradas: {len(zonas_e)}")

for z in zonas_e:
    print(f"\nZona E ID: {z['id']}")
    print(f"  Categoría: {z['categoria_nombre']} (ID: {z['categoria_id']})")
    print(f"  Creada: {z['created_at']}")
    
    # Contar partidos en esta zona
    cur.execute("""
        SELECT COUNT(*) as total
        FROM partidos
        WHERE zona_id = %s
    """, (z['id'],))
    
    total_partidos = cur.fetchone()['total']
    print(f"  Partidos: {total_partidos}")
    
    # Contar parejas (únicas en partidos)
    cur.execute("""
        SELECT DISTINCT pareja1_id as pareja_id
        FROM partidos
        WHERE zona_id = %s
        UNION
        SELECT DISTINCT pareja2_id as pareja_id
        FROM partidos
        WHERE zona_id = %s
    """, (z['id'], z['id']))
    
    parejas = cur.fetchall()
    print(f"  Parejas únicas: {len(parejas)}")

# Mostrar los partidos de cada zona
print("\n" + "=" * 80)
print("DETALLE DE PARTIDOS POR ZONA")
print("=" * 80)

for z in zonas_e:
    print(f"\n🔹 ZONA E (ID: {z['id']}) - {z['categoria_nombre']}")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            p.cancha_id,
            pu1.nombre || ' ' || pu1.apellido as j1_p1,
            pu2.nombre || ' ' || pu2.apellido as j2_p1,
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
    """, (z['id'],))
    
    partidos = cur.fetchall()
    
    if not partidos:
        print("  (Sin partidos)")
    else:
        for p in partidos:
            if p['fecha_hora']:
                print(f"\n  Partido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
            else:
                print(f"\n  Partido {p['id_partido']}: SIN HORARIO")
            print(f"    {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")

print("\n" + "=" * 80)
print("RECOMENDACIÓN")
print("=" * 80)

# Encontrar la zona correcta (la más reciente con partidos de Pansa)
cur.execute("""
    SELECT DISTINCT tz.id, tz.created_at
    FROM torneo_zonas tz
    JOIN partidos p ON p.zona_id = tz.id
    JOIN torneos_parejas tp ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
    JOIN perfil_usuarios pu ON (tp.jugador1_id = pu.id_usuario OR tp.jugador2_id = pu.id_usuario)
    WHERE tz.torneo_id = 46
    AND tz.nombre = 'Zona E'
    AND LOWER(pu.apellido) = 'pansa'
    ORDER BY tz.created_at DESC
    LIMIT 1
""")

zona_correcta = cur.fetchone()

if zona_correcta:
    print(f"\n✅ Zona correcta (con partidos de Pansa): ID {zona_correcta['id']}")
    print(f"   Creada: {zona_correcta['created_at']}")
    
    # Zonas a eliminar
    zonas_a_eliminar = [z['id'] for z in zonas_e if z['id'] != zona_correcta['id']]
    if zonas_a_eliminar:
        print(f"\n⚠️  Zonas duplicadas a eliminar: {zonas_a_eliminar}")
else:
    print("\n⚠️  No se encontró zona con partidos de Pansa")

cur.close()
conn.close()
