import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("REPROGRAMAR ZONA C - CONFIGURACIÓN FINAL")
print("=" * 80)

# Identificación de partidos:
# Pareja 1030: Luciano Paez / Juan Córdoba
# Pareja 1036: Facundo Martín / Pablo Samir
# Pareja 1037: Benjamin Palacios / Cristian Gurgone

# Partido 1163: Pareja 1036 (Samir) vs Pareja 1030 (Paez)
# Partido 1162: Pareja 1036 (Samir) vs Pareja 1037 (Gurgone)
# Partido 1164: Pareja 1037 (Gurgone) vs Pareja 1030 (Paez)

print("\n📋 REPROGRAMACIÓN SOLICITADA:")
print("-" * 80)
print("1. Viernes 16:00 - Luciano Paez vs Pablo Samir (Partido 1163)")
print("2. Viernes 18:00 - Cristian Gurgone vs Pablo Samir (Partido 1162)")
print("3. Viernes 20:30 - Cristian Gurgone vs Luciano Paez (Partido 1164)")

# 1. Partido 1163: Paez vs Samir → Viernes 16:00
print("\n1️⃣  Partido 1163 → Viernes 16:00")
print("-" * 80)

nuevo_horario_1163 = datetime(2026, 3, 27, 16, 0)

cur.execute("""
    UPDATE partidos
    SET fecha_hora = %s,
        cancha_id = 93
    WHERE id_partido = 1163
""", (nuevo_horario_1163,))

print(f"✅ Partido 1163 (Paez vs Samir) → {nuevo_horario_1163.strftime('%A %d/%m %H:%M')} - Cancha 93")

# 2. Partido 1162: Gurgone vs Samir → Viernes 18:00
print("\n2️⃣  Partido 1162 → Viernes 18:00")
print("-" * 80)

nuevo_horario_1162 = datetime(2026, 3, 27, 18, 0)

cur.execute("""
    UPDATE partidos
    SET fecha_hora = %s,
        cancha_id = 93
    WHERE id_partido = 1162
""", (nuevo_horario_1162,))

print(f"✅ Partido 1162 (Gurgone vs Samir) → {nuevo_horario_1162.strftime('%A %d/%m %H:%M')} - Cancha 93")

# 3. Partido 1164: Gurgone vs Paez → Viernes 20:30
print("\n3️⃣  Partido 1164 → Viernes 20:30")
print("-" * 80)

nuevo_horario_1164 = datetime(2026, 3, 27, 20, 30)

cur.execute("""
    UPDATE partidos
    SET fecha_hora = %s,
        cancha_id = 93
    WHERE id_partido = 1164
""", (nuevo_horario_1164,))

print(f"✅ Partido 1164 (Gurgone vs Paez) → {nuevo_horario_1164.strftime('%A %d/%m %H:%M')} - Cancha 93")

conn.commit()

# Verificación final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL - ZONA C")
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
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46
    AND tc.nombre = '5ta'
    AND tz.nombre = 'Zona C'
    ORDER BY p.fecha_hora
""")

partidos_zona_c = cur.fetchall()

for p in partidos_zona_c:
    print(f"\n✅ Partido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    print(f"   Pareja {p['pareja1_id']}: {p['j1_p1']} / {p['j2_p1']}")
    print(f"   vs")
    print(f"   Pareja {p['pareja2_id']}: {p['j1_p2']} / {p['j2_p2']}")

print("\n" + "=" * 80)
print("✅ ZONA C REPROGRAMADA CORRECTAMENTE")
print("=" * 80)
print("\nRESUMEN:")
print("  16:00 - Paez vs Samir")
print("  18:00 - Gurgone vs Samir")
print("  20:30 - Gurgone vs Paez")

cur.close()
conn.close()
