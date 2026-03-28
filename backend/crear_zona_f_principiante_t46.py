import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CREAR ZONA F - PRINCIPIANTE - TORNEO 46")
print("=" * 80)

# Datos de las parejas
parejas_data = [
    {"j1_nombre": "Alan", "j1_apellido": "Lucero", "j2_nombre": "Lautaro", "j2_apellido": "Macia"},
    {"j1_nombre": "Esteban", "j1_apellido": "Allendes", "j2_nombre": "Tiago", "j2_apellido": "Quintero"},
    {"j1_nombre": "Jonathan", "j1_apellido": "De la Vega", "j2_nombre": "Lucas", "j2_apellido": "Basualdo"}
]

# 1. Buscar o crear usuarios
print("\n1️⃣  BUSCAR/CREAR USUARIOS")
print("-" * 80)

usuarios_ids = {}

for p in parejas_data:
    for jugador in ['j1', 'j2']:
        nombre = p[f'{jugador}_nombre']
        apellido = p[f'{jugador}_apellido']
        key = f"{nombre}_{apellido}"
        
        # Buscar usuario existente
        cur.execute("""
            SELECT pu.id_usuario as id
            FROM perfil_usuarios pu
            WHERE LOWER(pu.nombre) = LOWER(%s)
            AND LOWER(pu.apellido) = LOWER(%s)
        """, (nombre, apellido))
        
        usuario = cur.fetchone()
        
        if usuario:
            usuarios_ids[key] = usuario['id']
            print(f"  ✓ {nombre} {apellido}: ID {usuario['id']} (ya existe)")
        else:
            # Crear usuario nuevo
            email = f"{nombre.lower()}.{apellido.lower()}@temp.com"
            username = f"{nombre.lower()}{apellido.lower()}"
            
            cur.execute("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id_usuario
            """, (username, email, 'temp_hash'))
            
            user_id = cur.fetchone()['id_usuario']
            
            cur.execute("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, fecha_nacimiento)
                VALUES (%s, %s, %s, '1990-01-01')
            """, (user_id, nombre, apellido))
            
            usuarios_ids[key] = user_id
            print(f"  ✅ {nombre} {apellido}: ID {user_id} (creado)")

conn.commit()

# 2. Crear Zona F
print("\n2️⃣  CREAR ZONA F")
print("-" * 80)

cur.execute("""
    INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
    VALUES (46, 125, 'Zona F', 6)
    RETURNING id
""")

zona_id = cur.fetchone()['id']
print(f"✅ Zona F creada: ID {zona_id}")

conn.commit()

# 3. Crear parejas
print("\n3️⃣  CREAR PAREJAS")
print("-" * 80)

parejas_ids = []

for p in parejas_data:
    j1_key = f"{p['j1_nombre']}_{p['j1_apellido']}"
    j2_key = f"{p['j2_nombre']}_{p['j2_apellido']}"
    
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
        VALUES (46, 125, 125, %s, %s, 'confirmada', 'aprobado', TRUE, FALSE)
        RETURNING id
    """, (usuarios_ids[j1_key], usuarios_ids[j2_key]))
    
    pareja_id = cur.fetchone()['id']
    parejas_ids.append(pareja_id)
    
    print(f"✅ Pareja {pareja_id}: {p['j1_nombre']} {p['j1_apellido']} / {p['j2_nombre']} {p['j2_apellido']}")
    
    # Insertar en torneo_zona_parejas
    cur.execute("""
        INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
        VALUES (%s, %s)
    """, (zona_id, pareja_id))

conn.commit()

# 4. Crear partidos (todos contra todos)
print("\n4️⃣  CREAR PARTIDOS")
print("-" * 80)

partidos = [
    {"p1": 0, "p2": 1, "fecha": "2026-03-28", "hora": "11:00", "cancha": 92},  # Lucero vs Allendes
    {"p1": 0, "p2": 2, "fecha": "2026-03-28", "hora": "15:00", "cancha": 93},  # Lucero vs De la Vega
    {"p1": 1, "p2": 2, "fecha": "2026-03-28", "hora": "19:00", "cancha": 94},  # Allendes vs De la Vega
]

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
            125,
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
        i,
        parejas_ids[partido['p1']],
        parejas_ids[partido['p2']],
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
    """, (parejas_ids[partido['p2']], parejas_ids[partido['p1']]))
    
    nombres = cur.fetchone()
    
    print(f"\n✅ Partido {partido_id}: {partido['fecha']} {partido['hora']} - Cancha {partido['cancha']}")
    print(f"   {nombres['j1_p1']}/{nombres['j2_p1']} vs {nombres['j1_p2']}/{nombres['j2_p2']}")

conn.commit()

# 5. Verificación final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL")
print("=" * 80)

cur.execute("""
    SELECT 
        tz.id as zona_id,
        tz.nombre as zona,
        COUNT(DISTINCT tzp.pareja_id) as parejas,
        COUNT(DISTINCT p.id_partido) as partidos
    FROM torneo_zonas tz
    LEFT JOIN torneo_zona_parejas tzp ON tz.id = tzp.zona_id
    LEFT JOIN partidos p ON tz.id = p.zona_id
    WHERE tz.id = %s
    GROUP BY tz.id, tz.nombre
""", (zona_id,))

stats = cur.fetchone()

print(f"\n✅ Zona F (ID {stats['zona_id']})")
print(f"   Parejas: {stats['parejas']}")
print(f"   Partidos: {stats['partidos']}")

# Verificar campos críticos de los partidos
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN tipo = 'torneo' THEN 1 END) as tipo_ok,
        COUNT(CASE WHEN id_torneo = 46 THEN 1 END) as torneo_ok,
        COUNT(CASE WHEN fase = 'zona' THEN 1 END) as fase_ok
    FROM partidos
    WHERE zona_id = %s
""", (zona_id,))

check = cur.fetchone()

print(f"\n   Partidos con tipo='torneo': {check['tipo_ok']}/{check['total']}")
print(f"   Partidos con id_torneo=46: {check['torneo_ok']}/{check['total']}")
print(f"   Partidos con fase='zona': {check['fase_ok']}/{check['total']}")

if check['total'] == check['tipo_ok'] == check['torneo_ok'] == check['fase_ok']:
    print("\n✅ TODOS LOS DATOS CORRECTOS - ZONA F LISTA")
else:
    print("\n⚠️  Hay datos incorrectos")

print("\n" + "=" * 80)
print("✅ ZONA F DE PRINCIPIANTE CREADA EXITOSAMENTE")
print("=" * 80)

cur.close()
conn.close()
