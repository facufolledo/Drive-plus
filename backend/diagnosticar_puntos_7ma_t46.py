import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("DIAGNOSTICAR PUNTOS 7MA - TORNEO 46")
print("=" * 80)

# PASO 1: Ver partidos de Zona A con resultados
print("\n1️⃣  PARTIDOS ZONA A CON RESULTADOS")
print("-" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.pareja1_id,
        p.pareja2_id,
        p.ganador_pareja_id,
        p.resultado_padel,
        p.estado,
        p.fase,
        p.zona_id,
        tz.nombre as zona_nombre
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE p.id_torneo = 46
    AND tz.categoria_id = 126
    AND tz.nombre = 'Zona A'
    ORDER BY p.id_partido
""")

partidos_a = cur.fetchall()

print(f"Partidos en Zona A: {len(partidos_a)}")
for p in partidos_a:
    print(f"  Partido {p['id_partido']}: P{p['pareja1_id']} vs P{p['pareja2_id']}")
    print(f"    Ganador: {p['ganador_pareja_id']}, Resultado: {p['resultado_padel']}, Estado: {p['estado']}")

# PASO 2: Calcular puntos manualmente para Zona A
print("\n2️⃣  CALCULAR PUNTOS MANUALMENTE ZONA A")
print("-" * 80)

cur.execute("""
    SELECT 
        tzp.pareja_id,
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneo_zona_parejas tzp
    JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    JOIN torneo_zonas tz ON tzp.zona_id = tz.id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 126
    AND tz.nombre = 'Zona A'
""")

parejas_a = cur.fetchall()

print(f"Parejas en Zona A: {len(parejas_a)}")

for pareja in parejas_a:
    pareja_id = pareja['pareja_id']
    
    # Contar victorias
    cur.execute("""
        SELECT COUNT(*) as victorias
        FROM partidos p
        JOIN torneo_zonas tz ON p.zona_id = tz.id
        WHERE p.id_torneo = 46
        AND tz.categoria_id = 126
        AND tz.nombre = 'Zona A'
        AND p.ganador_pareja_id = %s
        AND p.estado = 'finalizado'
    """, (pareja_id,))
    
    victorias = cur.fetchone()['victorias']
    puntos = victorias * 2
    
    print(f"  Pareja {pareja_id} ({pareja['j1']}/{pareja['j2']}): {victorias} victorias = {puntos} puntos")

# PASO 3: Verificar estado de TODOS los partidos de 7ma
print("\n3️⃣  ESTADO DE PARTIDOS 7MA")
print("-" * 80)

cur.execute("""
    SELECT 
        p.estado,
        COUNT(*) as total,
        COUNT(p.ganador_pareja_id) as con_ganador,
        COUNT(p.resultado_padel) as con_resultado
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE p.id_torneo = 46
    AND tz.categoria_id = 126
    AND p.fase = 'zona'
    GROUP BY p.estado
""")

estados = cur.fetchall()

print("Estados de partidos:")
for e in estados:
    print(f"  {e['estado']}: {e['total']} partidos ({e['con_ganador']} con ganador, {e['con_resultado']} con resultado)")

# PASO 4: Ver un partido específico con resultado
print("\n4️⃣  EJEMPLO PARTIDO CON RESULTADO")
print("-" * 80)

cur.execute("""
    SELECT 
        p.id_partido,
        p.pareja1_id,
        p.pareja2_id,
        p.ganador_pareja_id,
        p.resultado_padel,
        p.estado,
        tz.nombre as zona_nombre
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE p.id_torneo = 46
    AND tz.categoria_id = 126
    AND p.resultado_padel IS NOT NULL
    LIMIT 5
""")

ejemplos = cur.fetchall()

print(f"Ejemplos de partidos con resultado:")
for p in ejemplos:
    print(f"  Partido {p['id_partido']} ({p['zona_nombre']}): P{p['pareja1_id']} vs P{p['pareja2_id']}")
    print(f"    Resultado: {p['resultado_padel']}, Ganador: {p['ganador_pareja_id']}, Estado: {p['estado']}")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 80)
