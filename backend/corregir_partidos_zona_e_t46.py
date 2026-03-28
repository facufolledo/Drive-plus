import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CORREGIR PARTIDOS ZONA E - TORNEO 46")
print("=" * 80)

# Estado actual:
# Partido 1265: Viernes 16:00 - Pansa/Sanchez vs Banega/Banega (CORRECTO - se está jugando)
# Partido 1266: Viernes 21:30 - Macia/Alvarez vs Banega/Banega (INCORRECTO)
# Partido 1267: Sin horario - Pansa/Sanchez vs Macia/Alvarez (INCORRECTO)

# Debe ser:
# Partido 1265: Viernes 16:00 - Pansa/Sanchez vs Banega/Banega (CORRECTO)
# Partido 1266: Viernes 21:30 - Pansa/Sanchez vs Macia/Alvarez (CAMBIAR)
# Partido 1267: Sin horario - Macia/Alvarez vs Banega/Banega (CAMBIAR)

print("\n📋 CORRECCIÓN:")
print("-" * 80)
print("Partido 1266: Cambiar de Macia vs Banega → Pansa vs Macia (viernes 21:30)")
print("Partido 1267: Cambiar de Pansa vs Macia → Macia vs Banega (sin horario)")

# Obtener IDs de parejas
cur.execute("""
    SELECT 
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    JOIN torneo_zonas tz ON tp.categoria_id = tz.categoria_id
    WHERE tz.nombre = 'Zona E'
    AND tz.torneo_id = 46
    ORDER BY tp.id
""")

parejas = cur.fetchall()

print("\n📊 Parejas de Zona E:")
for p in parejas:
    print(f"  Pareja {p['id']}: {p['j1']} / {p['j2']}")

# Identificar parejas
pareja_pansa = None
pareja_banega = None
pareja_macia = None

for p in parejas:
    nombres = f"{p['j1']} {p['j2']}".lower()
    if 'pansa' in nombres:
        pareja_pansa = p['id']
    elif 'banega' in nombres and 'valentin' in nombres:
        pareja_banega = p['id']
    elif 'macia' in nombres:
        pareja_macia = p['id']

print(f"\nPareja Pansa: {pareja_pansa}")
print(f"Pareja Banega: {pareja_banega}")
print(f"Pareja Macia: {pareja_macia}")

# Corregir partido 1266: debe ser Pansa vs Macia
print("\n1️⃣  CORREGIR PARTIDO 1266")
print("-" * 80)

cur.execute("""
    UPDATE partidos
    SET pareja1_id = %s, pareja2_id = %s
    WHERE id_partido = 1266
""", (pareja_pansa, pareja_macia))

print(f"✅ Partido 1266 corregido: Pansa vs Macia (viernes 21:30)")

# Corregir partido 1267: debe ser Macia vs Banega
print("\n2️⃣  CORREGIR PARTIDO 1267")
print("-" * 80)

cur.execute("""
    UPDATE partidos
    SET pareja1_id = %s, pareja2_id = %s
    WHERE id_partido = 1267
""", (pareja_macia, pareja_banega))

print(f"✅ Partido 1267 corregido: Macia vs Banega (sin horario)")

conn.commit()

# Verificación final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL - ZONA E")
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
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE tz.nombre = 'Zona E'
    AND tz.torneo_id = 46
    ORDER BY p.fecha_hora NULLS LAST
""")

partidos = cur.fetchall()

for p in partidos:
    if p['fecha_hora']:
        print(f"\n✅ Partido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    else:
        print(f"\n⚠️  Partido {p['id_partido']}: SIN PROGRAMAR")
    print(f"   {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")

print("\n" + "=" * 80)
print("✅ PARTIDOS CORREGIDOS")
print("=" * 80)

cur.close()
conn.close()
