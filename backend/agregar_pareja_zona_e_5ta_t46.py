import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("AGREGAR PAREJA A ZONA E - 5TA - TORNEO 46")
print("=" * 80)

# 1. Buscar Zona E de 5ta
cur.execute("""
    SELECT tz.id
    FROM torneo_zonas tz
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 127
    AND tz.nombre = 'Zona E'
""")

zona = cur.fetchone()
zona_id = zona['id']
print(f"✅ Zona E de 5ta: ID {zona_id}")

# 2. Buscar usuarios
print("\n1️⃣  BUSCAR/CREAR USUARIOS")
print("-" * 80)

# Buscar Tebi Lopez
cur.execute("""
    SELECT pu.id_usuario as id
    FROM perfil_usuarios pu
    WHERE LOWER(pu.nombre) LIKE '%tebi%'
    OR LOWER(pu.apellido) LIKE '%lopez%'
""")

tebi_results = cur.fetchall()

print(f"\nBúsqueda 'Tebi Lopez': {len(tebi_results)} resultados")
for r in tebi_results:
    cur.execute("""
        SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = %s
    """, (r['id'],))
    perfil = cur.fetchone()
    print(f"  ID {r['id']}: {perfil['nombre']} {perfil['apellido']}")

# Buscar Joaquin Abrizuela
cur.execute("""
    SELECT pu.id_usuario as id
    FROM perfil_usuarios pu
    WHERE LOWER(pu.nombre) LIKE '%joaquin%'
    AND (LOWER(pu.apellido) LIKE '%abri%' OR LOWER(pu.apellido) LIKE '%briz%')
""")

joaquin_results = cur.fetchall()

print(f"\nBúsqueda 'Joaquin Abrizuela': {len(joaquin_results)} resultados")
for r in joaquin_results:
    cur.execute("""
        SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = %s
    """, (r['id'],))
    perfil = cur.fetchone()
    print(f"  ID {r['id']}: {perfil['nombre']} {perfil['apellido']}")

# Si no encontramos, buscar más amplio
if not tebi_results:
    print("\n⚠️  No se encontró Tebi Lopez, buscando variantes...")
    cur.execute("""
        SELECT pu.id_usuario as id, pu.nombre, pu.apellido
        FROM perfil_usuarios pu
        WHERE LOWER(pu.apellido) = 'lopez'
        ORDER BY pu.id_usuario DESC
        LIMIT 5
    """)
    lopez_results = cur.fetchall()
    print(f"  Usuarios con apellido Lopez:")
    for r in lopez_results:
        print(f"    ID {r['id']}: {r['nombre']} {r['apellido']}")

if not joaquin_results:
    print("\n⚠️  No se encontró Joaquin Abrizuela, buscando variantes...")
    cur.execute("""
        SELECT pu.id_usuario as id, pu.nombre, pu.apellido
        FROM perfil_usuarios pu
        WHERE LOWER(pu.nombre) = 'joaquin'
        ORDER BY pu.id_usuario DESC
        LIMIT 5
    """)
    joaquin_all = cur.fetchall()
    print(f"  Usuarios con nombre Joaquin:")
    for r in joaquin_all:
        print(f"    ID {r['id']}: {r['nombre']} {r['apellido']}")

print("\n" + "=" * 80)
print("SELECCIONAR IDs MANUALMENTE")
print("=" * 80)
print("\nPor favor, indica los IDs correctos:")
print("  Tebi Lopez: ID = ?")
print("  Joaquin Abrizuela: ID = ?")
print("\nO si no existen, se crearán nuevos usuarios.")

# Crear usuarios si no existen (usando nombres exactos)
tebi_id = None
joaquin_id = None

if tebi_results:
    tebi_id = tebi_results[0]['id']
    print(f"\n✓ Usando Tebi Lopez: ID {tebi_id}")
else:
    cur.execute("""
        INSERT INTO usuarios (nombre_usuario, email, password_hash)
        VALUES (%s, %s, %s)
        RETURNING id_usuario
    """, ('tebilopez', 'tebi.lopez@temp.com', 'temp_hash'))
    
    tebi_id = cur.fetchone()['id_usuario']
    
    cur.execute("""
        INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, fecha_nacimiento)
        VALUES (%s, %s, %s, '1990-01-01')
    """, (tebi_id, 'Tebi', 'Lopez'))
    
    print(f"\n✅ Tebi Lopez creado: ID {tebi_id}")

if joaquin_results:
    joaquin_id = joaquin_results[0]['id']
    print(f"✓ Usando Joaquin Abrizuela: ID {joaquin_id}")
else:
    cur.execute("""
        INSERT INTO usuarios (nombre_usuario, email, password_hash)
        VALUES (%s, %s, %s)
        RETURNING id_usuario
    """, ('joaquinabrizuela', 'joaquin.abrizuela@temp.com', 'temp_hash'))
    
    joaquin_id = cur.fetchone()['id_usuario']
    
    cur.execute("""
        INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, fecha_nacimiento)
        VALUES (%s, %s, %s, '1990-01-01')
    """, (joaquin_id, 'Joaquin', 'Abrizuela'))
    
    print(f"✅ Joaquin Abrizuela creado: ID {joaquin_id}")

conn.commit()

# 3. Crear pareja
print("\n2️⃣  CREAR PAREJA")
print("-" * 80)

cur.execute("""
    INSERT INTO torneos_parejas (
        torneo_id,
        categoria_id,
        categoria_asignada,
        jugador1_id,
        jugador2_id,
        estado,
        pago_estado,
        confirmado_jugador1,
        confirmado_jugador2
    )
    VALUES (46, 127, 127, %s, %s, 'confirmada', 'aprobado', TRUE, FALSE)
    RETURNING id
""", (tebi_id, joaquin_id))

pareja_id = cur.fetchone()['id']
print(f"✅ Pareja {pareja_id}: Tebi Lopez / Joaquin Abrizuela")

# Insertar en torneo_zona_parejas
cur.execute("""
    INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
    VALUES (%s, %s)
""", (zona_id, pareja_id))

conn.commit()

# 4. Obtener las otras 2 parejas de la zona
print("\n3️⃣  OBTENER PAREJAS EXISTENTES EN ZONA E")
print("-" * 80)

cur.execute("""
    SELECT 
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneo_zona_parejas tzp
    JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tzp.zona_id = %s
    AND tp.id != %s
    ORDER BY tp.id
""", (zona_id, pareja_id))

otras_parejas = cur.fetchall()

print(f"Parejas existentes en Zona E:")
for p in otras_parejas:
    print(f"  Pareja {p['id']}: {p['j1']} / {p['j2']}")

# 5. Crear los 2 partidos nuevos
print("\n4️⃣  CREAR PARTIDOS")
print("-" * 80)

partidos = [
    {"pareja2_id": otras_parejas[0]['id'], "fecha": "2026-03-28", "hora": "12:00", "cancha": 92},
    {"pareja2_id": otras_parejas[1]['id'], "fecha": "2026-03-28", "hora": "16:00", "cancha": 93},
]

# Contar partidos existentes para numero_partido
cur.execute("""
    SELECT COUNT(*) as total FROM partidos WHERE zona_id = %s
""", (zona_id,))

num_partidos_existentes = cur.fetchone()['total']

for i, partido in enumerate(partidos, 1):
    fecha_hora = f"{partido['fecha']} {partido['hora']}:00"
    
    cur.execute("""
        INSERT INTO partidos (
            tipo,
            id_torneo,
            categoria_id,
            zona_id,
            fase,
            numero_partido,
            pareja1_id,
            pareja2_id,
            fecha,
            fecha_hora,
            cancha_id,
            estado,
            id_creador
        )
        VALUES (
            'torneo',
            46,
            127,
            %s,
            'zona',
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            'pendiente',
            50
        )
        RETURNING id_partido
    """, (
        zona_id,
        num_partidos_existentes + i,
        pareja_id,
        partido['pareja2_id'],
        partido['fecha'],
        fecha_hora,
        partido['cancha']
    ))
    
    partido_id = cur.fetchone()['id_partido']
    
    # Obtener nombres
    cur.execute("""
        SELECT 
            pu1.nombre || ' ' || pu1.apellido as j1_p1,
            pu2.nombre || ' ' || pu2.apellido as j2_p1,
            pu3.nombre || ' ' || pu3.apellido as j1_p2,
            pu4.nombre || ' ' || pu4.apellido as j2_p2
        FROM torneos_parejas tp1
        JOIN torneos_parejas tp2 ON tp2.id = %s
        JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE tp1.id = %s
    """, (partido['pareja2_id'], pareja_id))
    
    nombres = cur.fetchone()
    
    print(f"\n✅ Partido {partido_id}: {partido['fecha']} {partido['hora']} - Cancha {partido['cancha']}")
    print(f"   {nombres['j1_p1']}/{nombres['j2_p1']} vs {nombres['j1_p2']}/{nombres['j2_p2']}")

conn.commit()

# 6. Verificación final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL - ZONA E DE 5TA")
print("=" * 80)

cur.execute("""
    SELECT 
        COUNT(DISTINCT tzp.pareja_id) as parejas,
        COUNT(DISTINCT p.id_partido) as partidos
    FROM torneo_zonas tz
    LEFT JOIN torneo_zona_parejas tzp ON tz.id = tzp.zona_id
    LEFT JOIN partidos p ON tz.id = p.zona_id
    WHERE tz.id = %s
    GROUP BY tz.id
""", (zona_id,))

stats = cur.fetchone()

print(f"\n✅ Zona E (ID {zona_id})")
print(f"   Parejas: {stats['parejas']}")
print(f"   Partidos: {stats['partidos']}")

# Mostrar todos los partidos
cur.execute("""
    SELECT 
        p.id_partido,
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
    WHERE p.zona_id = %s
    ORDER BY p.fecha_hora NULLS LAST
""", (zona_id,))

partidos_zona = cur.fetchall()

print(f"\nPartidos de Zona E:")
for p in partidos_zona:
    if p['fecha_hora']:
        print(f"\n  Partido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    else:
        print(f"\n  Partido {p['id_partido']}: SIN HORARIO")
    print(f"    {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")

print("\n" + "=" * 80)
print("✅ PAREJA AGREGADA Y PARTIDOS CREADOS")
print("=" * 80)

cur.close()
conn.close()
