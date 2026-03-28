import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("INSCRIBIR ZONA E - PRINCIPIANTE - TORNEO 46")
print("=" * 80)

# 1. Buscar Pansa Sergio
print("\n1️⃣  BUSCAR PANSA SERGIO")
print("-" * 80)

cur.execute("""
    SELECT id_usuario, nombre, apellido
    FROM perfil_usuarios
    WHERE LOWER(apellido) LIKE '%pansa%'
    AND LOWER(nombre) LIKE '%sergio%'
""")

pansa = cur.fetchone()

if pansa:
    print(f"✅ Encontrado: {pansa['nombre']} {pansa['apellido']} (ID: {pansa['id_usuario']})")
    pansa_id = pansa['id_usuario']
else:
    print("❌ No encontrado - necesito crear el usuario")
    pansa_id = None

# 2. Buscar o crear los demás jugadores
print("\n2️⃣  BUSCAR/CREAR JUGADORES")
print("-" * 80)

jugadores_nuevos = [
    ("Maxi", "Sanchez"),
    ("Valentin", "Banega"),
    ("Lautaro", "Banega"),
    ("Mauri", "Macia"),
    ("Mauri", "Alvarez")
]

jugadores_ids = {}

for nombre, apellido in jugadores_nuevos:
    cur.execute("""
        SELECT id_usuario, nombre, apellido
        FROM perfil_usuarios
        WHERE LOWER(nombre) = LOWER(%s)
        AND LOWER(apellido) = LOWER(%s)
    """, (nombre, apellido))
    
    jugador = cur.fetchone()
    
    if jugador:
        print(f"✅ {nombre} {apellido} ya existe (ID: {jugador['id_usuario']})")
        jugadores_ids[f"{nombre}_{apellido}"] = jugador['id_usuario']
    else:
        # Crear usuario nuevo
        email_temp = f"{nombre.lower()}.{apellido.lower()}@temp.com"
        
        # Primero crear en tabla usuarios
        cur.execute("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id_usuario
        """, (f"{nombre} {apellido}", email_temp, "temp_hash"))
        
        next_id = cur.fetchone()['id_usuario']
        
        # Luego crear en perfil_usuarios
        cur.execute("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
            VALUES (%s, %s, %s)
        """, (next_id, nombre, apellido))
        
        jugadores_ids[f"{nombre}_{apellido}"] = next_id
        print(f"✅ {nombre} {apellido} creado (ID: {next_id})")

# 3. Obtener categoría Principiante
print("\n3️⃣  OBTENER CATEGORÍA PRINCIPIANTE")
print("-" * 80)

cur.execute("""
    SELECT id
    FROM torneo_categorias
    WHERE torneo_id = 46
    AND nombre = 'Principiante'
""")

categoria = cur.fetchone()
categoria_id = categoria['id']
print(f"✅ Categoría Principiante ID: {categoria_id}")

# 4. Crear Zona E
print("\n4️⃣  CREAR ZONA E")
print("-" * 80)

cur.execute("""
    INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
    VALUES (46, %s, 'Zona E', 5)
    RETURNING id
""", (categoria_id,))

zona_e_id = cur.fetchone()['id']
print(f"✅ Zona E creada (ID: {zona_e_id})")

# 5. Inscribir parejas
print("\n5️⃣  INSCRIBIR PAREJAS")
print("-" * 80)

# Pareja 1: Pansa / Sanchez
if pansa_id:
    cur.execute("""
        INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, pago_estado)
        VALUES (46, %s, %s, %s, 'confirmada', 'aprobado')
        RETURNING id
    """, (categoria_id, pansa_id, jugadores_ids['Maxi_Sanchez']))
    
    pareja1_id = cur.fetchone()['id']
    print(f"✅ Pareja 1: Pansa / Sanchez (ID: {pareja1_id})")
else:
    print("⚠️  No se puede crear pareja Pansa/Sanchez - Pansa no encontrado")
    pareja1_id = None

# Pareja 2: Valentin Banega / Lautaro Banega
cur.execute("""
    INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, pago_estado)
    VALUES (46, %s, %s, %s, 'confirmada', 'aprobado')
    RETURNING id
""", (categoria_id, jugadores_ids['Valentin_Banega'], jugadores_ids['Lautaro_Banega']))

pareja2_id = cur.fetchone()['id']
print(f"✅ Pareja 2: Banega / Banega (ID: {pareja2_id})")

# Pareja 3: Mauri Macia / Mauri Alvarez
cur.execute("""
    INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, pago_estado)
    VALUES (46, %s, %s, %s, 'confirmada', 'aprobado')
    RETURNING id
""", (categoria_id, jugadores_ids['Mauri_Macia'], jugadores_ids['Mauri_Alvarez']))

pareja3_id = cur.fetchone()['id']
print(f"✅ Pareja 3: Macia / Alvarez (ID: {pareja3_id})")

# 6. Crear partidos
print("\n6️⃣  CREAR PARTIDOS")
print("-" * 80)

if pareja1_id:
    # Partido 1: Pansa vs Banega - Viernes 16:00 (YA SE ESTÁ JUGANDO)
    partido1_fecha = datetime(2026, 3, 27, 16, 0)
    partido1_fecha_solo = partido1_fecha.date()
    
    cur.execute("""
        INSERT INTO partidos (categoria_id, zona_id, pareja1_id, pareja2_id, fecha, fecha_hora, cancha_id, id_creador)
        VALUES (%s, %s, %s, %s, %s, %s, 92, 50)
        RETURNING id_partido
    """, (categoria_id, zona_e_id, pareja1_id, pareja2_id, partido1_fecha_solo, partido1_fecha))
    
    partido1_id = cur.fetchone()['id_partido']
    print(f"✅ Partido 1: Pansa/Sanchez vs Banega/Banega")
    print(f"   Viernes 27/03 16:00 - Cancha 92 (ID: {partido1_id})")
    print(f"   ⚠️  SE ESTÁ JUGANDO AHORA")

# Partido 2: Macia vs Banega - Viernes 21:30
partido2_fecha = datetime(2026, 3, 27, 21, 30)
partido2_fecha_solo = partido2_fecha.date()

# Verificar disponibilidad de cancha
cur.execute("""
    SELECT cancha_id, fecha_hora
    FROM partidos
    WHERE fecha_hora BETWEEN %s AND %s
    AND cancha_id IS NOT NULL
    ORDER BY cancha_id
""", (datetime(2026, 3, 27, 21, 20), datetime(2026, 3, 27, 22, 40)))

partidos_cercanos = cur.fetchall()

canchas_ocupadas = set()
for p in partidos_cercanos:
    print(f"  Cancha {p['cancha_id']}: {p['fecha_hora'].strftime('%H:%M')} (ocupada)")
    canchas_ocupadas.add(p['cancha_id'])

canchas_disponibles = [92, 93, 94]
canchas_libres = [c for c in canchas_disponibles if c not in canchas_ocupadas]

if canchas_libres:
    cancha_partido2 = canchas_libres[0]
    print(f"\n✅ Cancha {cancha_partido2} disponible para 21:30")
else:
    cancha_partido2 = 92
    print(f"\n⚠️  No hay canchas libres, usando Cancha {cancha_partido2}")

cur.execute("""
    INSERT INTO partidos (categoria_id, zona_id, pareja1_id, pareja2_id, fecha, fecha_hora, cancha_id, id_creador)
    VALUES (%s, %s, %s, %s, %s, %s, %s, 50)
    RETURNING id_partido
""", (categoria_id, zona_e_id, pareja3_id, pareja2_id, partido2_fecha_solo, partido2_fecha, cancha_partido2))

partido2_id = cur.fetchone()['id_partido']
print(f"✅ Partido 2: Macia/Alvarez vs Banega/Banega")
print(f"   Viernes 27/03 21:30 - Cancha {cancha_partido2} (ID: {partido2_id})")

# Partido 3: Pansa vs Macia - Sábado (sin horario aún)
if pareja1_id:
    partido3_fecha_solo = datetime(2026, 3, 28).date()
    
    cur.execute("""
        INSERT INTO partidos (categoria_id, zona_id, pareja1_id, pareja2_id, fecha, id_creador)
        VALUES (%s, %s, %s, %s, %s, 50)
        RETURNING id_partido
    """, (categoria_id, zona_e_id, pareja1_id, pareja3_id, partido3_fecha_solo))
    
    partido3_id = cur.fetchone()['id_partido']
    print(f"✅ Partido 3: Pansa/Sanchez vs Macia/Alvarez")
    print(f"   Sábado 28/03 - SIN HORARIO (ID: {partido3_id})")
    print(f"   ⚠️  Necesita horario para mañana")

conn.commit()

# Verificación final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL - ZONA E PRINCIPIANTE")
print("=" * 80)

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
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE tz.nombre = 'Zona E'
    AND tz.torneo_id = 46
    ORDER BY p.fecha_hora NULLS LAST
""")

partidos = cur.fetchall()

for p in partidos:
    if p['fecha_hora']:
        print(f"\n✅ Partido {p['id_partido']}: {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    else:
        print(f"\n⚠️  Partido {p['id_partido']}: SIN PROGRAMAR")
    print(f"   {p['j1_p1']}/{p['j2_p1']} vs {p['j1_p2']}/{p['j2_p2']}")

print("\n" + "=" * 80)
print("✅ ZONA E CREADA E INSCRITA")
print("=" * 80)

cur.close()
conn.close()
