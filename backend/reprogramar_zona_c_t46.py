import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("REPROGRAMAR ZONA C - TORNEO 46")
print("=" * 80)

# Cambios solicitados:
# 1. Partido 1162: Viernes 20:30
# 2. Partido 1164: Viernes 17:00
# 3. Partido 1163: Buscar horario sábado

print("\n1️⃣  Partido 1162 → Viernes 20:30")
print("-" * 80)

nuevo_horario_1162 = datetime(2026, 3, 27, 20, 30)

cur.execute("""
    UPDATE partidos
    SET fecha_hora = %s
    WHERE id_partido = 1162
""", (nuevo_horario_1162,))

print(f"✅ Partido 1162 movido a {nuevo_horario_1162.strftime('%A %d/%m %H:%M')}")

print("\n2️⃣  Partido 1164 → Viernes 17:00")
print("-" * 80)

nuevo_horario_1164 = datetime(2026, 3, 27, 17, 0)

cur.execute("""
    UPDATE partidos
    SET fecha_hora = %s
    WHERE id_partido = 1164
""", (nuevo_horario_1164,))

print(f"✅ Partido 1164 movido a {nuevo_horario_1164.strftime('%A %d/%m %H:%M')}")

print("\n3️⃣  Partido 1163 → Buscar horario sábado")
print("-" * 80)

# Verificar horarios disponibles el sábado
cur.execute("""
    SELECT 
        p.fecha_hora,
        p.cancha_id
    FROM partidos p
    WHERE p.id_torneo = 46
    AND EXTRACT(DOW FROM p.fecha_hora) = 6
    AND p.fecha_hora IS NOT NULL
    ORDER BY p.cancha_id, p.fecha_hora
""")

partidos_sabado = cur.fetchall()

print("Partidos programados el sábado:")
for p in partidos_sabado:
    print(f"  {p['fecha_hora'].strftime('%H:%M')} - Cancha {p['cancha_id']}")

# Sugerir horarios disponibles
print("\n💡 Horarios sugeridos para partido 1163 el sábado:")
print("  - 09:00 (temprano)")
print("  - 10:00")
print("  - 14:00")
print("  - 17:00")
print("  - 18:00")

print("\n⚠️  Partido 1163 NO movido - esperando confirmación de horario")

conn.commit()

# Verificar estado final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL - ZONA C")
print("=" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tp1.id as pareja1_id,
        tp2.id as pareja2_id
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    WHERE p.id_torneo = 46
    AND tc.nombre = '5ta'
    AND tz.nombre = 'Zona C'
    ORDER BY p.fecha_hora
""")

partidos_zona_c = cur.fetchall()

for p in partidos_zona_c:
    if p['fecha_hora']:
        print(f"\nPartido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    else:
        print(f"\nPartido {p['id_partido']}: SIN PROGRAMAR")
    print(f"  P{p['pareja1_id']} vs P{p['pareja2_id']}")

cur.close()
conn.close()
