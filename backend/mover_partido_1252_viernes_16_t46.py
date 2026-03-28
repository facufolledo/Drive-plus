import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("MOVER PARTIDO 1252 A VIERNES 16:00 - TORNEO 46")
print("=" * 80)

# Obtener info actual del partido
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
    WHERE p.id_partido = 1252
""")

partido = cur.fetchone()

print(f"\n📋 PARTIDO 1252 - {partido['categoria']} {partido['zona']}")
print(f"   {partido['j1_p1']} / {partido['j2_p1']}")
print(f"   vs")
print(f"   {partido['j1_p2']} / {partido['j2_p2']}")
print(f"\n   Horario actual: {partido['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {partido['cancha_id']}")

# Nuevo horario: Viernes 27/03/2026 16:00
nuevo_horario = datetime(2026, 3, 27, 16, 0)
nueva_cancha = 93

print(f"   Nuevo horario: {nuevo_horario.strftime('%A %d/%m %H:%M')} - Cancha {nueva_cancha}")

# Actualizar
cur.execute("""
    UPDATE partidos
    SET fecha_hora = %s,
        cancha_id = %s
    WHERE id_partido = 1252
""", (nuevo_horario, nueva_cancha))

conn.commit()

print(f"\n✅ PARTIDO MOVIDO EXITOSAMENTE")

# Verificar
cur.execute("""
    SELECT fecha_hora, cancha_id
    FROM partidos
    WHERE id_partido = 1252
""")

verificacion = cur.fetchone()
print(f"\n📊 VERIFICACIÓN:")
print(f"   Nuevo horario en BD: {verificacion['fecha_hora'].strftime('%A %d/%m %H:%M')}")
print(f"   Nueva cancha en BD: {verificacion['cancha_id']}")

cur.close()
conn.close()
