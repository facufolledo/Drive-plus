import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("ANALIZAR PARTIDOS 7MA - TORNEO 46")
print("=" * 80)

# Buscar TODOS los partidos de torneo 46 que podrían ser de 7ma
# Buscar por tipo='torneo', fase='zona', sin importar categoria_id
print("\n1️⃣  BUSCAR PARTIDOS DE ZONA SIN CATEGORIA_ID CORRECTA")
print("-" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.categoria_id,
        p.zona_id,
        p.estado,
        p.ganador_pareja_id,
        p.pareja1_id,
        p.pareja2_id,
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
    WHERE p.id_torneo = 46
    AND p.tipo = 'torneo'
    AND p.fase = 'zona'
    AND p.zona_id IS NULL
    ORDER BY p.id_partido
""")

partidos_sin_zona = cur.fetchall()

print(f"\nPartidos de zona SIN zona_id: {len(partidos_sin_zona)}")

if partidos_sin_zona:
    print("\nPrimeros 5 partidos:")
    for p in partidos_sin_zona[:5]:
        print(f"\n  Partido {p['id_partido']} - Cat {p['categoria_id']} - Estado: {p['estado']}")
        print(f"    {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")
        if p['ganador_pareja_id']:
            print(f"    Ganador: Pareja {p['ganador_pareja_id']}")

# Buscar partidos con zona_id pero categoria_id incorrecta
print("\n2️⃣  BUSCAR PARTIDOS CON ZONA_ID PERO CATEGORIA INCORRECTA")
print("-" * 80)

# Ver si hay partidos con zona_id que no coincide con la categoría de la zona
cur.execute("""
    SELECT 
        p.id_partido,
        p.categoria_id as partido_cat,
        p.zona_id,
        tz.categoria_id as zona_cat,
        tz.nombre as zona_nombre,
        p.estado,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1
    FROM partidos p
    LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    WHERE p.id_torneo = 46
    AND p.tipo = 'torneo'
    AND p.fase = 'zona'
    AND p.zona_id IS NOT NULL
    AND (tz.categoria_id IS NULL OR p.categoria_id != tz.categoria_id)
    ORDER BY p.id_partido
    LIMIT 10
""")

partidos_desincronizados = cur.fetchall()

print(f"\nPartidos con categoría desincronizada: {len(partidos_desincronizados)}")

if partidos_desincronizados:
    for p in partidos_desincronizados:
        print(f"\n  Partido {p['id_partido']}")
        print(f"    Partido.categoria_id: {p['partido_cat']}")
        print(f"    Zona.categoria_id: {p['zona_cat']}")
        print(f"    Zona: {p['zona_nombre']} (ID {p['zona_id']})")
        print(f"    Jugadores: {p['j1_p1']}/{p['j2_p1']} vs ...")

# Buscar parejas de 7ma que no están en zonas
print("\n3️⃣  PAREJAS DE 7MA SIN ZONA")
print("-" * 80)

# Primero necesito saber qué categoria_id es 7ma
# Voy a buscar parejas que tengan partidos y ver sus categorías
cur.execute("""
    SELECT DISTINCT
        tp.categoria_id,
        tp.categoria_asignada,
        COUNT(DISTINCT tp.id) as parejas,
        COUNT(DISTINCT p.id_partido) as partidos
    FROM torneos_parejas tp
    LEFT JOIN partidos p ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id) AND p.id_torneo = 46
    WHERE tp.torneo_id = 46
    GROUP BY tp.categoria_id, tp.categoria_asignada
    ORDER BY tp.categoria_id
""")

stats_parejas = cur.fetchall()

print("\nEstadísticas de parejas por categoría:")
for s in stats_parejas:
    print(f"  categoria_id={s['categoria_id']}, asignada={s['categoria_asignada']}: {s['parejas']} parejas, {s['partidos']} partidos")

cur.close()
conn.close()
