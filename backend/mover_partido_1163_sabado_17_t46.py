import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("MOVER PARTIDO 1163 - SÁBADO 17:00")
print("=" * 80)

# Verificar estado actual del partido
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tc.nombre as categoria,
        tz.nombre as zona,
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
    WHERE p.id_partido = 1163
""")

partido = cur.fetchone()

print(f"\n📋 PARTIDO 1163 - {partido['categoria']} {partido['zona']}")
print(f"   Horario actual: {partido['fecha_hora'].strftime('%A %d/%m %H:%M') if partido['fecha_hora'] else 'SIN PROGRAMAR'}")
print(f"   Cancha actual: {partido['cancha_id'] if partido['cancha_id'] else 'SIN ASIGNAR'}")
print(f"   Pareja {partido['pareja1_id']}: {partido['j1_p1']} / {partido['j2_p1']}")
print(f"   vs")
print(f"   Pareja {partido['pareja2_id']}: {partido['j1_p2']} / {partido['j2_p2']}")

# Verificar disponibilidad de canchas el sábado 17:00
nuevo_horario = datetime(2026, 3, 28, 17, 0)

print(f"\n🔍 Verificando disponibilidad para {nuevo_horario.strftime('%A %d/%m %H:%M')}")
print("-" * 80)

cur.execute("""
    SELECT cancha_id, fecha_hora
    FROM partidos
    WHERE id_torneo = 46
    AND fecha_hora BETWEEN %s AND %s
    AND cancha_id IS NOT NULL
    ORDER BY cancha_id
""", (datetime(2026, 3, 28, 16, 50), datetime(2026, 3, 28, 18, 20)))

partidos_cercanos = cur.fetchall()

canchas_ocupadas = set()
for p in partidos_cercanos:
    print(f"  Cancha {p['cancha_id']}: {p['fecha_hora'].strftime('%H:%M')} (ocupada)")
    canchas_ocupadas.add(p['cancha_id'])

# Canchas disponibles
canchas_disponibles = [92, 93, 94]
canchas_libres = [c for c in canchas_disponibles if c not in canchas_ocupadas]

print(f"\n✅ Canchas disponibles: {canchas_libres}")

# Elegir primera cancha disponible
cancha_elegida = canchas_libres[0] if canchas_libres else 92

print(f"\n💡 Asignando Cancha {cancha_elegida}")

# Mover partido
cur.execute("""
    UPDATE partidos
    SET fecha_hora = %s,
        cancha_id = %s
    WHERE id_partido = 1163
""", (nuevo_horario, cancha_elegida))

conn.commit()

print(f"\n✅ Partido 1163 movido a {nuevo_horario.strftime('%A %d/%m %H:%M')} - Cancha {cancha_elegida}")

# Verificación final de Zona C completa
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL - ZONA C COMPLETA")
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
print("✅ ZONA C COMPLETAMENTE REPROGRAMADA")
print("=" * 80)

cur.close()
conn.close()
