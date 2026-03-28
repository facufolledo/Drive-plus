import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("BUSCAR ALVAREZ REGISTRADO")
print("=" * 80)

# Buscar todos los Alvarez
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
    ORDER BY u.id_usuario DESC
""")

alvarez_users = cur.fetchall()

print(f"\nUsuarios con apellido Alvarez: {len(alvarez_users)}")

for user in alvarez_users:
    es_temp = '@temp.com' in user['email'] or '@example.com' in user['email']
    tipo = "TEMP" if es_temp else "REAL"
    
    print(f"\n  [{tipo}] ID {user['id_usuario']}: {user['nombre']} {user['apellido']}")
    print(f"    Username: {user['nombre_usuario']}")
    print(f"    Email: {user['email']}")
    
    # Ver si tiene parejas en T46
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
    """, (user['id_usuario'], user['id_usuario'], user['id_usuario']))
    
    parejas = cur.fetchall()
    if parejas:
        print(f"    Parejas en T46:")
        for p in parejas:
            print(f"      - Pareja {p['id']}: con {p['compañero']}")

# Buscar también Barrionuevo
print("\n" + "=" * 80)
print("BUSCAR BARRIONUEVO")
print("=" * 80)

cur.execute("""
    SELECT 
        u.id_usuario,
        u.nombre_usuario,
        u.email,
        pu.nombre,
        pu.apellido
    FROM usuarios u
    JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
    WHERE LOWER(pu.apellido) LIKE '%barrionuevo%'
    ORDER BY u.id_usuario DESC
""")

barrionuevo_users = cur.fetchall()

print(f"\nUsuarios con apellido Barrionuevo: {len(barrionuevo_users)}")

for user in barrionuevo_users:
    es_temp = '@temp.com' in user['email'] or '@example.com' in user['email']
    tipo = "TEMP" if es_temp else "REAL"
    
    print(f"\n  [{tipo}] ID {user['id_usuario']}: {user['nombre']} {user['apellido']}")
    print(f"    Username: {user['nombre_usuario']}")
    print(f"    Email: {user['email']}")
    
    # Ver si tiene parejas en T46
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
    """, (user['id_usuario'], user['id_usuario'], user['id_usuario']))
    
    parejas = cur.fetchall()
    if parejas:
        print(f"    Parejas en T46:")
        for p in parejas:
            print(f"      - Pareja {p['id']}: con {p['compañero']}")

cur.close()
conn.close()
