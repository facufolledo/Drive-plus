import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("SINCRONIZAR TORNEO_ZONA_PAREJAS - 7MA TORNEO 46")
print("=" * 80)

# PASO 1: Obtener todas las zonas de 7ma (categoria_id=126)
print("\n1️⃣  OBTENER ZONAS DE 7MA")
print("-" * 80)

cur.execute("""
    SELECT id, nombre, numero_orden, categoria_id
    FROM torneo_zonas
    WHERE torneo_id = 46
    AND categoria_id = 126
    ORDER BY numero_orden
""")

zonas = cur.fetchall()

print(f"Zonas de 7ma encontradas: {len(zonas)}")
for z in zonas:
    print(f"  ID {z['id']}: {z['nombre']} (orden {z['numero_orden']})")

# PASO 2: Extraer parejas de cada zona desde los partidos
print("\n2️⃣  EXTRAER PAREJAS DESDE PARTIDOS")
print("-" * 80)

parejas_por_zona = {}  # {zona_id: [pareja_ids]}

for zona in zonas:
    zona_id = zona['id']
    zona_nombre = zona['nombre']
    
    cur.execute("""
        SELECT DISTINCT
            CASE 
                WHEN p.pareja1_id IS NOT NULL THEN p.pareja1_id
                ELSE p.pareja2_id
            END as pareja_id
        FROM partidos p
        WHERE p.id_torneo = 46
        AND p.zona_id = %s
        AND p.fase = 'zona'
        
        UNION
        
        SELECT DISTINCT
            CASE 
                WHEN p.pareja2_id IS NOT NULL THEN p.pareja2_id
                ELSE p.pareja1_id
            END as pareja_id
        FROM partidos p
        WHERE p.id_torneo = 46
        AND p.zona_id = %s
        AND p.fase = 'zona'
    """, (zona_id, zona_id))
    
    parejas = [r['pareja_id'] for r in cur.fetchall() if r['pareja_id']]
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
        """, (parejas,))
        
        for p in cur.fetchall():
            print(f"    Pareja {p['id']}: {p['j1']}/{p['j2']}")

# PASO 3: Verificar estado actual de torneo_zona_parejas
print("\n3️⃣  VERIFICAR ESTADO ACTUAL")
print("-" * 80)

cur.execute("""
    SELECT zona_id, pareja_id
    FROM torneo_zona_parejas
    WHERE zona_id IN (
        SELECT id FROM torneo_zonas WHERE torneo_id = 46 AND categoria_id = 126
    )
""")

actual = cur.fetchall()
actual_set = {(r['zona_id'], r['pareja_id']) for r in actual}

print(f"Registros actuales en torneo_zona_parejas: {len(actual)}")

# PASO 4: Identificar diferencias
print("\n4️⃣  IDENTIFICAR DIFERENCIAS")
print("-" * 80)

faltantes = []
for zona_id, parejas in parejas_por_zona.items():
    for pareja_id in parejas:
        if (zona_id, pareja_id) not in actual_set:
            faltantes.append((zona_id, pareja_id))

print(f"\nParejas FALTANTES en torneo_zona_parejas: {len(faltantes)}")

if faltantes:
    print("\nDetalle de faltantes:")
    for zona_id, pareja_id in faltantes:
        zona_nombre = next((z['nombre'] for z in zonas if z['id'] == zona_id), f"Zona {zona_id}")
        print(f"  {zona_nombre}: Pareja {pareja_id}")

# PASO 5: Insertar faltantes
if faltantes:
    print("\n5️⃣  INSERTAR PAREJAS FALTANTES")
    print("-" * 80)
    
    respuesta = input(f"\n¿Insertar {len(faltantes)} parejas en torneo_zona_parejas? (s/n): ")
    
    if respuesta.lower() == 's':
        for zona_id, pareja_id in faltantes:
            cur.execute("""
                INSERT INTO torneo_zona_parejas (zona_id, pareja_id, clasificado)
                VALUES (%s, %s, false)
                ON CONFLICT DO NOTHING
            """, (zona_id, pareja_id))
        
        conn.commit()
        print(f"\n✅ {len(faltantes)} parejas insertadas correctamente")
        
        # Verificar
        cur.execute("""
            SELECT COUNT(*) as total
            FROM torneo_zona_parejas
            WHERE zona_id IN (
                SELECT id FROM torneo_zonas WHERE torneo_id = 46 AND categoria_id = 126
            )
        """)
        
        total_final = cur.fetchone()['total']
        print(f"Total registros en torneo_zona_parejas para 7ma: {total_final}")
        print(f"Esperado: 8 zonas × 3 parejas = 24")
    else:
        print("\n❌ Operación cancelada")
else:
    print("\n✅ No hay parejas faltantes. torneo_zona_parejas está completo.")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("SINCRONIZACIÓN COMPLETADA")
print("=" * 80)
