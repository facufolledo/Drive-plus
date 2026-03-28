import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR DISPONIBILIDAD PARTIDO 1260 - VIERNES 17:00")
print("=" * 80)

# Obtener info del partido 1260
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tp1.id as pareja1_id,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        tp1.disponibilidad_horaria as restricciones_p1,
        tp2.id as pareja2_id,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2,
        tp2.disponibilidad_horaria as restricciones_p2
    FROM partidos p
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_partido = 1260
""")

partido = cur.fetchone()

if not partido:
    print("❌ Partido 1260 no encontrado")
    cur.close()
    conn.close()
    exit(1)

print(f"\n📋 PARTIDO 1260")
print(f"  Horario actual: {partido['fecha_hora'].strftime('%A %d/%m %H:%M')}")
print(f"  Cancha actual: {partido['cancha_id']}")
print(f"  P{partido['pareja1_id']}: {partido['j1_p1']} / {partido['j2_p1']}")
print(f"  P{partido['pareja2_id']}: {partido['j1_p2']} / {partido['j2_p2']}")

# Verificar restricciones de las parejas
print(f"\n🚫 RESTRICCIONES:")

print(f"\n  Pareja {partido['pareja1_id']} ({partido['j1_p1']}/{partido['j2_p1']}):")
if partido['restricciones_p1']:
    for r in partido['restricciones_p1']:
        dias = ', '.join(r['dias'])
        print(f"    - NO disponible {dias} de {r['horaInicio']} a {r['horaFin']}")
else:
    print(f"    ✅ Sin restricciones")

print(f"\n  Pareja {partido['pareja2_id']} ({partido['j1_p2']}/{partido['j2_p2']}):")
if partido['restricciones_p2']:
    for r in partido['restricciones_p2']:
        dias = ', '.join(r['dias'])
        print(f"    - NO disponible {dias} de {r['horaInicio']} a {r['horaFin']}")
else:
    print(f"    ✅ Sin restricciones")

# Verificar disponibilidad viernes 17:00
print(f"\n" + "=" * 80)
print("DISPONIBILIDAD VIERNES 17:00")
print("=" * 80)

# Verificar si las parejas pueden jugar viernes 17:00
def puede_jugar(restricciones, dia, hora):
    if not restricciones:
        return True
    
    for r in restricciones:
        if dia.lower() in [d.lower() for d in r['dias']]:
            hora_inicio = r['horaInicio']
            hora_fin = r['horaFin']
            if hora_inicio <= hora < hora_fin:
                return False
    return True

puede_p1 = puede_jugar(partido['restricciones_p1'], 'viernes', '17:00')
puede_p2 = puede_jugar(partido['restricciones_p2'], 'viernes', '17:00')

print(f"\n✅ Pareja {partido['pareja1_id']}: {'SÍ puede' if puede_p1 else '❌ NO puede'} jugar viernes 17:00")
print(f"✅ Pareja {partido['pareja2_id']}: {'SÍ puede' if puede_p2 else '❌ NO puede'} jugar viernes 17:00")

if not (puede_p1 and puede_p2):
    print(f"\n❌ NO SE PUEDE MOVER - Una o ambas parejas tienen restricciones")
    cur.close()
    conn.close()
    exit(0)

# Verificar canchas disponibles viernes 17:00
cur.execute("""
    SELECT 
        p.id_partido,
        p.cancha_id,
        p.fecha_hora,
        tc.nombre as categoria
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    WHERE p.id_torneo = 46
    AND p.fecha_hora >= '2026-03-27 17:00:00'
    AND p.fecha_hora < '2026-03-27 18:10:00'
    ORDER BY p.cancha_id, p.fecha_hora
""")

partidos_viernes_17 = cur.fetchall()

canchas_ocupadas = set()
for p in partidos_viernes_17:
    canchas_ocupadas.add(p['cancha_id'])
    print(f"\n  Cancha {p['cancha_id']}: Partido {p['id_partido']} ({p['categoria']}) - {p['fecha_hora'].strftime('%H:%M')}")

# Obtener todas las canchas del torneo
cur.execute("""
    SELECT id, nombre
    FROM torneo_canchas
    WHERE torneo_id = 46
    AND activa = true
    ORDER BY id
""")

todas_canchas = cur.fetchall()
canchas_disponibles = [c for c in todas_canchas if c['id'] not in canchas_ocupadas]

print(f"\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)

if canchas_disponibles:
    print(f"\n✅ HAY {len(canchas_disponibles)} CANCHA(S) DISPONIBLE(S) VIERNES 17:00:")
    for c in canchas_disponibles:
        print(f"  - Cancha {c['id']}: {c['nombre']}")
    print(f"\n✅ SE PUEDE MOVER EL PARTIDO 1260 A VIERNES 17:00")
else:
    print(f"\n❌ NO HAY CANCHAS DISPONIBLES VIERNES 17:00")
    print(f"   Todas las canchas están ocupadas")

cur.close()
conn.close()
