import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("ANALIZAR PROBLEMA MACIA")
print("=" * 80)

# Ver el temp 1154
print("\n1️⃣  TEMP 1154 (Mauri Macia)")
print("-" * 80)

cur.execute("""
    SELECT 
        u.id_usuario,
        u.nombre_usuario,
        u.email,
        pu.nombre,
        pu.apellido
    FROM usuarios u
    JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
    WHERE u.id_usuario = 1154
""")

temp = cur.fetchone()
print(f"ID {temp['id_usuario']}: {temp['nombre']} {temp['apellido']}")
print(f"  Email: {temp['email']}")

# Ver pareja 1070
cur.execute("""
    SELECT 
        tp.id,
        tp.jugador1_id,
        tp.jugador2_id,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tp.id = 1070
""")

pareja = cur.fetchone()
print(f"\nPareja 1070:")
print(f"  Jugador 1 (ID {pareja['jugador1_id']}): {pareja['j1']}")
print(f"  Jugador 2 (ID {pareja['jugador2_id']}): {pareja['j2']}")

# Ver los dos usuarios reales
print("\n2️⃣  USUARIOS REALES")
print("-" * 80)

for user_id in [1156, 1162]:
    cur.execute("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            u.email,
            pu.nombre,
            pu.apellido
        FROM usuarios u
        JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
        WHERE u.id_usuario = %s
    """, (user_id,))
    
    real = cur.fetchone()
    print(f"\nID {real['id_usuario']}: {real['nombre']} {real['apellido']}")
    print(f"  Username: {real['nombre_usuario']}")
    print(f"  Email: {real['email']}")

# Buscar si hay otro temp "Alvarez"
print("\n3️⃣  BUSCAR TEMP ALVAREZ")
print("-" * 80)

cur.execute("""
    SELECT 
        u.id_usuario,
        u.nombre_usuario,
        u.email,
        pu.nombre,
        pu.apellido
    FROM usuarios u
    JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
    WHERE LOWER(pu.apellido) = 'alvarez'
    AND (u.email LIKE '%@temp.com' OR u.email LIKE '%@example.com')
""")

temps_alvarez = cur.fetchall()

if temps_alvarez:
    print(f"Temps con apellido Alvarez:")
    for t in temps_alvarez:
        print(f"\n  ID {t['id_usuario']}: {t['nombre']} {t['apellido']}")
        print(f"    Email: {t['email']}")
        
        # Ver si tiene parejas
        cur.execute("""
            SELECT 
                tp.id,
                CASE 
                    WHEN tp.jugador1_id = %s THEN pu2.nombre || ' ' || pu2.apellido
                    ELSE pu1.nombre || ' ' || pu1.apellido
                END as compañero
            FROM torneos_parejas tp
            LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE (tp.jugador1_id = %s OR tp.jugador2_id = %s)
            AND tp.torneo_id = 46
        """, (t['id_usuario'], t['id_usuario'], t['id_usuario']))
        
        parejas = cur.fetchall()
        if parejas:
            print(f"    Parejas en T46:")
            for p in parejas:
                print(f"      - Pareja {p['id']}: con {p['compañero']}")

print("\n" + "=" * 80)
print("ANÁLISIS")
print("=" * 80)

print("\nPareja 1070 tiene:")
if pareja['jugador1_id'] == 1154:
    print(f"  - Jugador 1: ID 1154 (Mauri Macia) - TEMP")
    print(f"  - Jugador 2: ID {pareja['jugador2_id']} ({pareja['j2']})")
    print(f"\n  → Mauri Macia debería ser Mauricio Macia (1156) o Lautaro Macia (1162)?")
else:
    print(f"  - Jugador 1: ID {pareja['jugador1_id']} ({pareja['j1']})")
    print(f"  - Jugador 2: ID 1154 (Mauri Macia) - TEMP")
    print(f"\n  → Mauri Macia debería ser Mauricio Macia (1156) o Lautaro Macia (1162)?")

print("\nNecesito que me digas:")
print("  - ¿Mauri Macia (temp 1154) es Mauricio (1156) o Lautaro (1162)?")
print("  - ¿Hay algún temp para Alvarez que deba migrarse también?")

cur.close()
conn.close()
