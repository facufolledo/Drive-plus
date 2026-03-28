import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("REVERTIR MIGRACIÓN INCORRECTA DE LAUTARO MACIA")
print("=" * 80)

# 1. Revertir: Lautaro (1162) → Mauri temp (1154)
print("\n1️⃣  REVERTIR: 1162 → 1154")
print("-" * 80)

# Actualizar torneos_parejas
cur.execute("""
    UPDATE torneos_parejas
    SET jugador1_id = 1154
    WHERE jugador1_id = 1162
    AND torneo_id = 46
    RETURNING id
""")

parejas_revertidas = cur.fetchall()
if parejas_revertidas:
    print(f"✅ {len(parejas_revertidas)} parejas revertidas (jugador1_id)")
    for p in parejas_revertidas:
        print(f"   - Pareja {p['id']}")

cur.execute("""
    UPDATE torneos_parejas
    SET jugador2_id = 1154
    WHERE jugador2_id = 1162
    AND torneo_id = 46
    RETURNING id
""")

parejas_revertidas2 = cur.fetchall()
if parejas_revertidas2:
    print(f"✅ {len(parejas_revertidas2)} parejas revertidas (jugador2_id)")

conn.commit()

# 2. Buscar TODOS los Macia
print("\n" + "=" * 80)
print("2️⃣  TODOS LOS MACIA EN LA BASE DE DATOS")
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
    WHERE LOWER(pu.apellido) = 'macia'
    ORDER BY u.id_usuario
""")

macias = cur.fetchall()

print(f"\nTotal usuarios Macia: {len(macias)}")

for macia in macias:
    es_temp = '@temp.com' in macia['email'] or '@example.com' in macia['email']
    tipo = "TEMP" if es_temp else "REAL"
    
    print(f"\n[{tipo}] ID {macia['id_usuario']}: {macia['nombre']} {macia['apellido']}")
    print(f"  Username: {macia['nombre_usuario']}")
    print(f"  Email: {macia['email']}")
    
    # Ver parejas en T46
    cur.execute("""
        SELECT 
            tp.id,
            tp.jugador1_id,
            tp.jugador2_id,
            CASE 
                WHEN tp.jugador1_id = %s THEN pu2.nombre || ' ' || pu2.apellido
                ELSE pu1.nombre || ' ' || pu1.apellido
            END as compañero
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE (tp.jugador1_id = %s OR tp.jugador2_id = %s)
        AND tp.torneo_id = 46
    """, (macia['id_usuario'], macia['id_usuario'], macia['id_usuario']))
    
    parejas = cur.fetchall()
    if parejas:
        print(f"  Parejas en T46:")
        for p in parejas:
            print(f"    - Pareja {p['id']}: con {p['compañero']}")

print("\n" + "=" * 80)
print("ANÁLISIS")
print("=" * 80)

print("\nUsuarios registrados que mencionaste:")
print("  - ID 1156: Mauricio Macia (mauriciomacia89@gmail.com)")
print("  - ID 1162: Lautaro Macia (lautaromacia888@gmail.com)")

print("\nTemps que creamos:")
print("  - ID 1154: Mauri Macia (@temp.com) - Pareja 1070 con Mauri Alvarez")

print("\n¿Cuál es cuál?")
print("  - ¿Mauri Macia (1154) es Mauricio (1156)?")
print("  - ¿O hay otro temp para Lautaro?")

cur.close()
conn.close()
