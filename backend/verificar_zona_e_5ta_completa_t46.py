import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR ZONA E - 5TA - TORNEO 46")
print("=" * 80)

# Buscar Zona E de 5ta
cur.execute("""
    SELECT tz.id
    FROM torneo_zonas tz
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 127
    AND tz.nombre = 'Zona E'
""")

zona = cur.fetchone()
zona_id = zona['id']

print(f"Zona E de 5ta: ID {zona_id}")

# Ver todas las parejas
print("\n" + "=" * 80)
print("PAREJAS EN ZONA E")
print("=" * 80)

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
""", (zona_id,))

parejas = cur.fetchall()

print(f"\nTotal parejas: {len(parejas)}")
for p in parejas:
    print(f"  Pareja {p['id']}: {p['j1']} / {p['j2']}")

# Ver todos los partidos
print("\n" + "=" * 80)
print("PARTIDOS EN ZONA E")
print("=" * 80)

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
""", (zona_id,))

partidos = cur.fetchall()

print(f"\nTotal partidos: {len(partidos)}")
for p in partidos:
    if p['fecha_hora']:
        print(f"\n  Partido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    else:
        print(f"\n  Partido {p['id_partido']}: SIN HORARIO")
    print(f"    {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")

# Verificar si hay partido Navarro/Loto vs Carrizo/Estrada
print("\n" + "=" * 80)
print("VERIFICAR PARTIDO FALTANTE")
print("=" * 80)

# Buscar pareja Navarro/Loto
cur.execute("""
    SELECT tp.id
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tp.torneo_id = 46
    AND (
        (LOWER(pu1.apellido) = 'navarro' AND LOWER(pu2.apellido) = 'loto')
        OR (LOWER(pu1.apellido) = 'loto' AND LOWER(pu2.apellido) = 'navarro')
    )
""")

pareja_navarro = cur.fetchone()

# Buscar pareja Carrizo/Estrada
cur.execute("""
    SELECT tp.id
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tp.torneo_id = 46
    AND (
        (LOWER(pu1.apellido) = 'carrizo' AND LOWER(pu2.apellido) = 'estrada')
        OR (LOWER(pu1.apellido) = 'estrada' AND LOWER(pu2.apellido) = 'carrizo')
    )
""")

pareja_carrizo = cur.fetchone()

if pareja_navarro and pareja_carrizo:
    print(f"\nPareja Navarro/Loto: ID {pareja_navarro['id']}")
    print(f"Pareja Carrizo/Estrada: ID {pareja_carrizo['id']}")
    
    # Verificar si existe partido entre ellas
    cur.execute("""
        SELECT id_partido
        FROM partidos
        WHERE zona_id = %s
        AND (
            (pareja1_id = %s AND pareja2_id = %s)
            OR (pareja1_id = %s AND pareja2_id = %s)
        )
    """, (zona_id, pareja_navarro['id'], pareja_carrizo['id'], pareja_carrizo['id'], pareja_navarro['id']))
    
    partido_existente = cur.fetchone()
    
    if partido_existente:
        print(f"\n✓ Ya existe partido entre Navarro/Loto y Carrizo/Estrada: {partido_existente['id_partido']}")
    else:
        print(f"\n⚠️  FALTA partido entre Navarro/Loto y Carrizo/Estrada")
        print(f"   Necesitamos crear este partido")

print("\n" + "=" * 80)
print("ANÁLISIS")
print("=" * 80)

if len(parejas) == 3 and len(partidos) == 3:
    print("\n✅ Zona E tiene 3 parejas y 3 partidos (todos contra todos)")
elif len(parejas) == 3 and len(partidos) < 3:
    print(f"\n⚠️  Zona E tiene 3 parejas pero solo {len(partidos)} partidos")
    print(f"   Faltan {3 - len(partidos)} partidos")
else:
    print(f"\n⚠️  Zona E tiene {len(parejas)} parejas y {len(partidos)} partidos")

cur.close()
conn.close()
