import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("FIX FINAL PARTIDOS ZONA E - TORNEO 46")
print("=" * 80)

# Actualizar todos los campos necesarios
cur.execute("""
    UPDATE partidos
    SET 
        tipo = 'torneo',
        id_torneo = 46,
        fase = 'zona'
    WHERE zona_id = 426
""")

print(f"✅ {cur.rowcount} partidos actualizados")

conn.commit()

# Verificación
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL")
print("=" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.tipo,
        p.id_torneo,
        p.fase,
        p.estado,
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
    WHERE p.zona_id = 426
    ORDER BY p.id_partido
""")

partidos = cur.fetchall()

for p in partidos:
    print(f"\n✅ Partido {p['id_partido']}")
    print(f"   Tipo: {p['tipo']} | Torneo: {p['id_torneo']} | Fase: {p['fase']} | Estado: {p['estado']}")
    if p['fecha_hora']:
        print(f"   {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    else:
        print(f"   SIN HORARIO")
    print(f"   {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")

print("\n" + "=" * 80)
print("✅ PARTIDOS CORREGIDOS - DEBERÍAN APARECER EN EL FRONTEND")
print("=" * 80)

cur.close()
conn.close()
