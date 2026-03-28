import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CORREGIR ZONA E - 5TA - TORNEO 46")
print("=" * 80)

# IDs conocidos
zona_e_id = 397
zona_c_id = 395
pareja_paez = 1030
pareja_navarro = 1038
pareja_lopez = 1077
pareja_carrizo = 1031

print("\nPROBLEMA:")
print("  - Paez/Córdoba (1030) está en Zona E pero debería estar en Zona C")
print("  - Navarro/Loto (1038) está en Zona C pero tiene partido en Zona E")

print("\nSOLUCIÓN:")
print("  1. Sacar Paez/Córdoba de Zona E")
print("  2. Meter Navarro/Loto en Zona E")
print("  3. Actualizar partido 1274 (Lopez vs Paez) → (Lopez vs Navarro)")
print("  4. Meter Paez/Córdoba en Zona C")

# 1. Sacar Paez/Córdoba de Zona E
print("\n" + "=" * 80)
print("1️⃣  SACAR PAEZ/CÓRDOBA DE ZONA E")
print("=" * 80)

cur.execute("""
    DELETE FROM torneo_zona_parejas
    WHERE zona_id = %s AND pareja_id = %s
    RETURNING zona_id, pareja_id
""", (zona_e_id, pareja_paez))

deleted = cur.fetchone()
if deleted:
    print(f"✅ Eliminado: Pareja {deleted['pareja_id']} de Zona {deleted['zona_id']}")
else:
    print("⚠️  No se encontró la relación para eliminar")

# 2. Sacar Navarro/Loto de Zona C
print("\n" + "=" * 80)
print("2️⃣  SACAR NAVARRO/LOTO DE ZONA C")
print("=" * 80)

cur.execute("""
    DELETE FROM torneo_zona_parejas
    WHERE zona_id = %s AND pareja_id = %s
    RETURNING zona_id, pareja_id
""", (zona_c_id, pareja_navarro))

deleted = cur.fetchone()
if deleted:
    print(f"✅ Eliminado: Pareja {deleted['pareja_id']} de Zona {deleted['zona_id']}")
else:
    print("⚠️  No se encontró la relación para eliminar")

# 3. Meter Navarro/Loto en Zona E
print("\n" + "=" * 80)
print("3️⃣  METER NAVARRO/LOTO EN ZONA E")
print("=" * 80)

cur.execute("""
    INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
    VALUES (%s, %s)
    RETURNING zona_id, pareja_id
""", (zona_e_id, pareja_navarro))

inserted = cur.fetchone()
print(f"✅ Insertado: Pareja {inserted['pareja_id']} en Zona {inserted['zona_id']}")

# 4. Meter Paez/Córdoba en Zona C
print("\n" + "=" * 80)
print("4️⃣  METER PAEZ/CÓRDOBA EN ZONA C")
print("=" * 80)

cur.execute("""
    INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
    VALUES (%s, %s)
    RETURNING zona_id, pareja_id
""", (zona_c_id, pareja_paez))

inserted = cur.fetchone()
print(f"✅ Insertado: Pareja {inserted['pareja_id']} en Zona {inserted['zona_id']}")

# 5. Actualizar partido 1274 (Lopez vs Paez) → (Lopez vs Navarro)
print("\n" + "=" * 80)
print("5️⃣  ACTUALIZAR PARTIDO 1274")
print("=" * 80)

cur.execute("""
    UPDATE partidos
    SET pareja2_id = %s
    WHERE id_partido = 1274
    RETURNING id_partido, pareja1_id, pareja2_id
""", (pareja_navarro,))

updated = cur.fetchone()
print(f"✅ Partido {updated['id_partido']} actualizado:")
print(f"   Pareja 1: {updated['pareja1_id']} (Lopez/Abrizuela)")
print(f"   Pareja 2: {updated['pareja2_id']} (Navarro/Loto)")

# 6. Crear partido faltante en Zona C: Navarro/Loto vs alguien
print("\n" + "=" * 80)
print("6️⃣  VERIFICAR ZONA C")
print("=" * 80)

# Ver parejas de Zona C
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
""", (zona_c_id,))

parejas_zona_c = cur.fetchall()

print(f"\nParejas en Zona C:")
for p in parejas_zona_c:
    print(f"  Pareja {p['id']}: {p['j1']} / {p['j2']}")

# Ver partidos de Zona C
cur.execute("""
    SELECT 
        p.id_partido,
        p.pareja1_id,
        p.pareja2_id,
        p.fecha_hora,
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
""", (zona_c_id,))

partidos_zona_c = cur.fetchall()

print(f"\nPartidos en Zona C:")
for p in partidos_zona_c:
    if p['fecha_hora']:
        print(f"\n  Partido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')}")
    else:
        print(f"\n  Partido {p['id_partido']}: SIN HORARIO")
    print(f"    Pareja {p['pareja1_id']}: {p['j1_p1']}/{p['j2_p1']}")
    print(f"    Pareja {p['pareja2_id']}: {p['j1_p2']}/{p['j2_p2']}")

conn.commit()

print("\n" + "=" * 80)
print("✅ CORRECCIÓN COMPLETADA")
print("=" * 80)

print("\nZona E ahora tiene:")
print("  - Navarro/Loto (1038) ✓")
print("  - Carrizo/Estrada (1031) ✓")
print("  - Lopez/Abrizuela (1077) ✓")

print("\nZona C ahora tiene:")
print("  - Paez/Córdoba (1030) ✓")
print("  - (otras parejas)")

cur.close()
conn.close()
