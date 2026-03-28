import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("RECREAR TORNEO_ZONA_PAREJAS - 7MA TORNEO 46")
print("=" * 80)

# PASO 1: Obtener zonas de 7ma
print("\n1️⃣  OBTENER ZONAS DE 7MA (categoria_id=126)")
print("-" * 80)

cur.execute("""
    SELECT id, nombre, numero_orden
    FROM torneo_zonas
    WHERE torneo_id = 46
    AND categoria_id = 126
    ORDER BY numero_orden
""")

zonas = cur.fetchall()
print(f"Zonas encontradas: {len(zonas)}")
for z in zonas:
    print(f"  ID {z['id']}: {z['nombre']}")

# PASO 2: Extraer parejas de cada zona desde partidos
print("\n2️⃣  EXTRAER PAREJAS DESDE PARTIDOS")
print("-" * 80)

parejas_por_zona = {}

for zona in zonas:
    zona_id = zona['id']
    zona_nombre = zona['nombre']
    
    # Obtener todas las parejas que jugaron en esta zona
    cur.execute("""
        SELECT DISTINCT pareja_id
        FROM (
            SELECT pareja1_id as pareja_id
            FROM partidos
            WHERE id_torneo = 46
            AND zona_id = %s
            AND fase = 'zona'
            AND pareja1_id IS NOT NULL
            
            UNION
            
            SELECT pareja2_id as pareja_id
            FROM partidos
            WHERE id_torneo = 46
            AND zona_id = %s
            AND fase = 'zona'
            AND pareja2_id IS NOT NULL
        ) parejas
        ORDER BY pareja_id
    """, (zona_id, zona_id))
    
    parejas = [r['pareja_id'] for r in cur.fetchall()]
    parejas_por_zona[zona_id] = parejas
    
    print(f"\n{zona_nombre} (ID {zona_id}): {len(parejas)} parejas")
    
    # Mostrar nombres
    if parejas:
        cur.execute("""
            SELECT 
                tp.id,
                pu1.nombre || ' ' || pu1.apellido as j1,
                pu2.nombre || ' ' || pu2.apellido as j2
            FROM torneos_parejas tp
            JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tp.id = ANY(%s)
            ORDER BY tp.id
        """, (parejas,))
        
        for p in cur.fetchall():
            print(f"    Pareja {p['id']}: {p['j1']}/{p['j2']}")

# PASO 3: Verificar estado actual
print("\n3️⃣  ESTADO ACTUAL DE TORNEO_ZONA_PAREJAS")
print("-" * 80)

cur.execute("""
    SELECT tzp.zona_id, tzp.pareja_id, tz.nombre
    FROM torneo_zona_parejas tzp
    JOIN torneo_zonas tz ON tzp.zona_id = tz.id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 126
    ORDER BY tz.numero_orden, tzp.pareja_id
""")

actual = cur.fetchall()
print(f"Registros actuales: {len(actual)}")

# Agrupar por zona
actual_por_zona = {}
for r in actual:
    zona_id = r['zona_id']
    if zona_id not in actual_por_zona:
        actual_por_zona[zona_id] = []
    actual_por_zona[zona_id].append(r['pareja_id'])

for zona in zonas:
    zona_id = zona['id']
    parejas_actual = actual_por_zona.get(zona_id, [])
    print(f"  {zona['nombre']}: {len(parejas_actual)} parejas en torneo_zona_parejas")

# PASO 4: Comparar y mostrar diferencias
print("\n4️⃣  COMPARAR ACTUAL vs PARTIDOS")
print("-" * 80)

total_esperado = sum(len(p) for p in parejas_por_zona.values())
total_actual = len(actual)

print(f"Total esperado (desde partidos): {total_esperado}")
print(f"Total actual (en torneo_zona_parejas): {total_actual}")

if total_esperado != total_actual:
    print(f"\n⚠️  DESINCRONIZACIÓN DETECTADA")
    
    for zona in zonas:
        zona_id = zona['id']
        esperadas = set(parejas_por_zona.get(zona_id, []))
        actuales = set(actual_por_zona.get(zona_id, []))
        
        faltantes = esperadas - actuales
        sobrantes = actuales - esperadas
        
        if faltantes or sobrantes:
            print(f"\n  {zona['nombre']}:")
            if faltantes:
                print(f"    Faltan: {faltantes}")
            if sobrantes:
                print(f"    Sobran: {sobrantes}")

# PASO 5: Recrear torneo_zona_parejas
print("\n5️⃣  RECREAR TORNEO_ZONA_PAREJAS")
print("-" * 80)

respuesta = input(f"\n¿Eliminar y recrear torneo_zona_parejas para 7ma? (s/n): ")

if respuesta.lower() == 's':
    # Eliminar registros actuales de 7ma
    cur.execute("""
        DELETE FROM torneo_zona_parejas
        WHERE zona_id IN (
            SELECT id FROM torneo_zonas WHERE torneo_id = 46 AND categoria_id = 126
        )
    """)
    
    eliminados = cur.rowcount
    print(f"\n✅ Eliminados {eliminados} registros antiguos")
    
    # Insertar nuevos registros
    insertados = 0
    for zona in zonas:
        zona_id = zona['id']
        parejas = parejas_por_zona.get(zona_id, [])
        
        for pareja_id in parejas:
            cur.execute("""
                INSERT INTO torneo_zona_parejas (zona_id, pareja_id, clasificado)
                VALUES (%s, %s, false)
            """, (zona_id, pareja_id))
            insertados += 1
    
    conn.commit()
    print(f"✅ Insertados {insertados} registros nuevos")
    
    # Verificar resultado final
    cur.execute("""
        SELECT COUNT(*) as total
        FROM torneo_zona_parejas tzp
        JOIN torneo_zonas tz ON tzp.zona_id = tz.id
        WHERE tz.torneo_id = 46
        AND tz.categoria_id = 126
    """)
    
    total_final = cur.fetchone()['total']
    print(f"\nTotal final en torneo_zona_parejas: {total_final}")
    print(f"Esperado: {total_esperado}")
    
    if total_final == total_esperado:
        print("\n✅ SINCRONIZACIÓN EXITOSA")
    else:
        print(f"\n⚠️  Diferencia: {total_final} vs {total_esperado}")
else:
    print("\n❌ Operación cancelada")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("PROCESO COMPLETADO")
print("=" * 80)
