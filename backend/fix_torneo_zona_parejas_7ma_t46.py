import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("FIX TORNEO_ZONA_PAREJAS - 7MA TORNEO 46")
print("=" * 80)

# PASO 1: Obtener zonas de 7ma
cur.execute("""
    SELECT id, nombre, numero_orden
    FROM torneo_zonas
    WHERE torneo_id = 46
    AND categoria_id = 126
    ORDER BY numero_orden
""")

zonas = cur.fetchall()
print(f"\n1️⃣  Zonas de 7ma: {len(zonas)}")

# PASO 2: Extraer parejas correctas desde partidos
print("\n2️⃣  EXTRAER PAREJAS CORRECTAS DESDE PARTIDOS")
print("-" * 80)

parejas_correctas = {}  # {zona_id: set(pareja_ids)}

for zona in zonas:
    zona_id = zona['id']
    
    cur.execute("""
        SELECT DISTINCT pareja_id
        FROM (
            SELECT pareja1_id as pareja_id
            FROM partidos
            WHERE id_torneo = 46 AND zona_id = %s AND fase = 'zona' AND pareja1_id IS NOT NULL
            UNION
            SELECT pareja2_id as pareja_id
            FROM partidos
            WHERE id_torneo = 46 AND zona_id = %s AND fase = 'zona' AND pareja2_id IS NOT NULL
        ) p
    """, (zona_id, zona_id))
    
    parejas_correctas[zona_id] = set(r['pareja_id'] for r in cur.fetchall())

# PASO 3: Obtener estado actual de torneo_zona_parejas
print("\n3️⃣  ESTADO ACTUAL DE TORNEO_ZONA_PAREJAS")
print("-" * 80)

cur.execute("""
    SELECT tzp.id, tzp.zona_id, tzp.pareja_id, tz.nombre
    FROM torneo_zona_parejas tzp
    JOIN torneo_zonas tz ON tzp.zona_id = tz.id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 126
""")

actual = cur.fetchall()
print(f"Registros actuales: {len(actual)}")

actual_por_zona = {}  # {zona_id: set(pareja_ids)}
ids_por_zona_pareja = {}  # {(zona_id, pareja_id): id}

for r in actual:
    zona_id = r['zona_id']
    if zona_id not in actual_por_zona:
        actual_por_zona[zona_id] = set()
    actual_por_zona[zona_id].add(r['pareja_id'])
    ids_por_zona_pareja[(zona_id, r['pareja_id'])] = r['id']

# PASO 4: Identificar cambios necesarios
print("\n4️⃣  IDENTIFICAR CAMBIOS")
print("-" * 80)

a_eliminar = []  # [(id, zona_nombre, pareja_id)]
a_insertar = []  # [(zona_id, zona_nombre, pareja_id)]

for zona in zonas:
    zona_id = zona['id']
    zona_nombre = zona['nombre']
    
    correctas = parejas_correctas.get(zona_id, set())
    actuales = actual_por_zona.get(zona_id, set())
    
    # Parejas que sobran (están en torneo_zona_parejas pero no en partidos)
    sobrantes = actuales - correctas
    for pareja_id in sobrantes:
        id_registro = ids_por_zona_pareja.get((zona_id, pareja_id))
        a_eliminar.append((id_registro, zona_nombre, pareja_id))
    
    # Parejas que faltan (están en partidos pero no en torneo_zona_parejas)
    faltantes = correctas - actuales
    for pareja_id in faltantes:
        a_insertar.append((zona_id, zona_nombre, pareja_id))

print(f"\nParejas a ELIMINAR: {len(a_eliminar)}")
if a_eliminar:
    for id_reg, zona_nombre, pareja_id in a_eliminar[:10]:
        print(f"  {zona_nombre}: Pareja {pareja_id} (ID registro: {id_reg})")

print(f"\nParejas a INSERTAR: {len(a_insertar)}")
if a_insertar:
    for zona_id, zona_nombre, pareja_id in a_insertar[:10]:
        # Obtener nombres
        cur.execute("""
            SELECT 
                pu1.nombre || ' ' || pu1.apellido as j1,
                pu2.nombre || ' ' || pu2.apellido as j2
            FROM torneos_parejas tp
            JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tp.id = %s
        """, (pareja_id,))
        
        nombres = cur.fetchone()
        if nombres:
            print(f"  {zona_nombre}: Pareja {pareja_id} ({nombres['j1']}/{nombres['j2']})")
        else:
            print(f"  {zona_nombre}: Pareja {pareja_id}")

# PASO 5: Aplicar cambios
if a_eliminar or a_insertar:
    print("\n5️⃣  APLICAR CAMBIOS")
    print("-" * 80)
    
    respuesta = input(f"\n¿Aplicar cambios? (Eliminar {len(a_eliminar)}, Insertar {len(a_insertar)}) (s/n): ")
    
    if respuesta.lower() == 's':
        # Eliminar sobrantes
        for id_reg, zona_nombre, pareja_id in a_eliminar:
            cur.execute("DELETE FROM torneo_zona_parejas WHERE id = %s", (id_reg,))
            print(f"  ❌ Eliminado: {zona_nombre} - Pareja {pareja_id}")
        
        # Insertar faltantes
        for zona_id, zona_nombre, pareja_id in a_insertar:
            cur.execute("""
                INSERT INTO torneo_zona_parejas (zona_id, pareja_id, clasificado)
                VALUES (%s, %s, false)
            """, (zona_id, pareja_id))
            print(f"  ✅ Insertado: {zona_nombre} - Pareja {pareja_id}")
        
        conn.commit()
        
        # Verificar resultado
        cur.execute("""
            SELECT COUNT(*) as total
            FROM torneo_zona_parejas tzp
            JOIN torneo_zonas tz ON tzp.zona_id = tz.id
            WHERE tz.torneo_id = 46
            AND tz.categoria_id = 126
        """)
        
        total_final = cur.fetchone()['total']
        total_esperado = sum(len(p) for p in parejas_correctas.values())
        
        print(f"\n✅ CAMBIOS APLICADOS")
        print(f"Total final: {total_final}")
        print(f"Esperado: {total_esperado}")
        
        if total_final == total_esperado:
            print("✅ SINCRONIZACIÓN EXITOSA")
        else:
            print(f"⚠️  Diferencia: {total_final} vs {total_esperado}")
    else:
        print("\n❌ Operación cancelada")
else:
    print("\n✅ No hay cambios necesarios. torneo_zona_parejas está sincronizado con los partidos.")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("PROCESO COMPLETADO")
print("=" * 80)
