import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("DIAGNOSTICAR CONFUSIÓN ZONA E - 5TA")
print("=" * 80)

# Buscar pareja Navarro/Loto (1038)
print("\n1️⃣  PAREJA NAVARRO/LOTO (1038)")
print("-" * 80)

cur.execute("""
    SELECT 
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2,
        tp.categoria_id,
        tp.categoria_asignada
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tp.id = 1038
""")

navarro_loto = cur.fetchone()
print(f"Pareja {navarro_loto['id']}: {navarro_loto['j1']} / {navarro_loto['j2']}")
print(f"  categoria_id: {navarro_loto['categoria_id']}")
print(f"  categoria_asignada: {navarro_loto['categoria_asignada']}")

# Ver en qué zona está
cur.execute("""
    SELECT 
        tz.id as zona_id,
        tz.nombre as zona_nombre,
        tz.categoria_id
    FROM torneo_zona_parejas tzp
    JOIN torneo_zonas tz ON tzp.zona_id = tz.id
    WHERE tzp.pareja_id = 1038
""")

zona_navarro = cur.fetchone()

if zona_navarro:
    print(f"\n✓ Navarro/Loto está en: {zona_navarro['zona_nombre']} (ID {zona_navarro['zona_id']}) - Categoría {zona_navarro['categoria_id']}")
else:
    print(f"\n⚠️  Navarro/Loto NO está en ninguna zona (torneo_zona_parejas)")

# Buscar pareja Paez/Córdoba (1030)
print("\n2️⃣  PAREJA PAEZ/CÓRDOBA (1030)")
print("-" * 80)

cur.execute("""
    SELECT 
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2,
        tp.categoria_id,
        tp.categoria_asignada
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tp.id = 1030
""")

paez_cordoba = cur.fetchone()
print(f"Pareja {paez_cordoba['id']}: {paez_cordoba['j1']} / {paez_cordoba['j2']}")
print(f"  categoria_id: {paez_cordoba['categoria_id']}")
print(f"  categoria_asignada: {paez_cordoba['categoria_asignada']}")

# Ver en qué zona está
cur.execute("""
    SELECT 
        tz.id as zona_id,
        tz.nombre as zona_nombre,
        tz.categoria_id
    FROM torneo_zona_parejas tzp
    JOIN torneo_zonas tz ON tzp.zona_id = tz.id
    WHERE tzp.pareja_id = 1030
""")

zona_paez = cur.fetchone()

if zona_paez:
    print(f"\n✓ Paez/Córdoba está en: {zona_paez['zona_nombre']} (ID {zona_paez['zona_id']}) - Categoría {zona_paez['categoria_id']}")
else:
    print(f"\n⚠️  Paez/Córdoba NO está en ninguna zona (torneo_zona_parejas)")

# Ver todos los partidos de Zona E (ID 397)
print("\n3️⃣  TODOS LOS PARTIDOS DE ZONA E (ID 397)")
print("-" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.pareja1_id,
        p.pareja2_id,
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
    WHERE p.zona_id = 397
    ORDER BY p.fecha_hora NULLS LAST
""")

partidos = cur.fetchall()

print(f"\nTotal partidos: {len(partidos)}")
for p in partidos:
    if p['fecha_hora']:
        print(f"\n  Partido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    else:
        print(f"\n  Partido {p['id_partido']}: SIN HORARIO")
    print(f"    Pareja {p['pareja1_id']}: {p['j1_p1']}/{p['j2_p1']}")
    print(f"    Pareja {p['pareja2_id']}: {p['j1_p2']}/{p['j2_p2']}")

print("\n" + "=" * 80)
print("RESUMEN DEL PROBLEMA")
print("=" * 80)

print("\nLa Zona E de 5ta debería tener:")
print("  - Navarro/Loto (1038)")
print("  - Carrizo/Estrada (1031)")
print("  - Lopez/Abrizuela (1077)")

print("\nPero actualmente tiene en torneo_zona_parejas:")
print("  - Paez/Córdoba (1030) ❌")
print("  - Carrizo/Estrada (1031) ✓")
print("  - Lopez/Abrizuela (1077) ✓")

print("\nY el partido 1168 usa Navarro/Loto (1038) que NO está en la zona")

cur.close()
conn.close()
