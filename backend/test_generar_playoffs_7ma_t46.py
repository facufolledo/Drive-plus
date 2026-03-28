import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("TEST GENERAR PLAYOFFS 7MA - TORNEO 46")
print("=" * 80)

# PASO 1: Verificar clasificados por zona
print("\n1️⃣  VERIFICAR CLASIFICADOS POR ZONA")
print("-" * 80)

cur.execute("""
    SELECT 
        tz.id as zona_id,
        tz.nombre as zona_nombre,
        tz.numero_orden,
        COUNT(DISTINCT tzp.pareja_id) as parejas_en_zona
    FROM torneo_zonas tz
    LEFT JOIN torneo_zona_parejas tzp ON tz.id = tzp.zona_id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 126
    GROUP BY tz.id, tz.nombre, tz.numero_orden
    ORDER BY tz.numero_orden
""")

zonas = cur.fetchall()

print(f"Zonas de 7ma: {len(zonas)}")
for z in zonas:
    print(f"  {z['zona_nombre']}: {z['parejas_en_zona']} parejas")

# PASO 2: Simular obtención de clasificados (lo que hace el servicio)
print("\n2️⃣  SIMULAR OBTENCIÓN DE CLASIFICADOS")
print("-" * 80)

clasificados = []

for zona in zonas:
    zona_id = zona['zona_id']
    zona_nombre = zona['zona_nombre']
    
    # Obtener parejas de la zona con sus puntos calculados
    cur.execute("""
        SELECT 
            tzp.pareja_id,
            tp.id,
            pu1.nombre || ' ' || pu1.apellido as j1,
            pu2.nombre || ' ' || pu2.apellido as j2,
            -- Calcular puntos desde partidos
            COALESCE(SUM(CASE 
                WHEN p.ganador_pareja_id = tzp.pareja_id THEN 2
                ELSE 0
            END), 0) as puntos,
            COUNT(p.id_partido) as pj
        FROM torneo_zona_parejas tzp
        JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
        JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN partidos p ON (p.pareja1_id = tzp.pareja_id OR p.pareja2_id = tzp.pareja_id)
            AND p.zona_id = tzp.zona_id
            AND p.fase = 'zona'
            AND p.estado = 'finalizado'
        WHERE tzp.zona_id = %s
        GROUP BY tzp.pareja_id, tp.id, pu1.nombre, pu1.apellido, pu2.nombre, pu2.apellido
        ORDER BY puntos DESC, pj DESC
        LIMIT 2
    """, (zona_id,))
    
    parejas_zona = cur.fetchall()
    
    print(f"\n{zona_nombre}:")
    for i, p in enumerate(parejas_zona):
        posicion = i + 1
        clasificados.append({
            'pareja_id': p['pareja_id'],
            'posicion': posicion,
            'puntos': p['puntos'],
            'zona_nombre': zona_nombre
        })
        print(f"  {posicion}° - Pareja {p['pareja_id']}: {p['j1']}/{p['j2']} ({p['puntos']} pts)")

print(f"\nTotal clasificados: {len(clasificados)}")
print(f"Esperado: 8 zonas × 2 = 16 clasificados")

# PASO 3: Verificar que todas las zonas tengan 2 clasificados
print("\n3️⃣  VERIFICAR CLASIFICADOS POR ZONA")
print("-" * 80)

zonas_con_clasificados = {}
for c in clasificados:
    zona = c['zona_nombre']
    if zona not in zonas_con_clasificados:
        zonas_con_clasificados[zona] = []
    zonas_con_clasificados[zona].append(c)

print(f"Zonas con clasificados: {len(zonas_con_clasificados)}")

problema = False
for zona, clases in zonas_con_clasificados.items():
    if len(clases) != 2:
        print(f"  ⚠️  {zona}: {len(clases)} clasificados (esperado: 2)")
        problema = True
    else:
        print(f"  ✅ {zona}: 2 clasificados")

if problema:
    print("\n⚠️  PROBLEMA: Algunas zonas no tienen exactamente 2 clasificados")
    print("Esto causará el error 'list index out of range' al generar playoffs")
else:
    print("\n✅ Todas las zonas tienen 2 clasificados. Playoffs debería funcionar.")

# PASO 4: Verificar playoffs existentes
print("\n4️⃣  VERIFICAR PLAYOFFS EXISTENTES")
print("-" * 80)

cur.execute("""
    SELECT fase, COUNT(*) as total
    FROM partidos
    WHERE id_torneo = 46
    AND categoria_id = 126
    AND fase IN ('16avos', '8vos', '4tos', 'semis', 'final')
    GROUP BY fase
    ORDER BY 
        CASE fase
            WHEN '16avos' THEN 1
            WHEN '8vos' THEN 2
            WHEN '4tos' THEN 3
            WHEN 'semis' THEN 4
            WHEN 'final' THEN 5
        END
""")

playoffs_existentes = cur.fetchall()

if playoffs_existentes:
    print("Playoffs ya generados:")
    for p in playoffs_existentes:
        print(f"  {p['fase']}: {p['total']} partidos")
    print("\n⚠️  Si quieres regenerar, primero elimina los playoffs existentes desde el frontend")
else:
    print("✅ No hay playoffs generados. Puedes generar desde el frontend.")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("TEST COMPLETADO")
print("=" * 80)
