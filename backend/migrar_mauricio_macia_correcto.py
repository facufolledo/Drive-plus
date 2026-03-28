import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("MIGRAR MAURICIO MACIA CORRECTAMENTE")
print("=" * 80)

# Migración: Mauri Macia (1154 temp) → Mauricio Macia (1156 real)
id_temp = 1154
id_real = 1156

print(f"\n🔴 TEMP: Mauri Macia (ID {id_temp})")
print(f"🟢 REAL: Mauricio Macia (ID {id_real})")

# 1. Actualizar torneos_parejas (jugador1_id)
print(f"\n1️⃣  Actualizar torneos_parejas (jugador1_id)")
cur.execute("""
    UPDATE torneos_parejas
    SET jugador1_id = %s
    WHERE jugador1_id = %s
    RETURNING id, jugador1_id, jugador2_id
""", (id_real, id_temp))

parejas_j1 = cur.fetchall()
if parejas_j1:
    for p in parejas_j1:
        # Obtener nombres
        cur.execute("""
            SELECT 
                pu1.nombre || ' ' || pu1.apellido as j1,
                pu2.nombre || ' ' || pu2.apellido as j2
            FROM torneos_parejas tp
            JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tp.id = %s
        """, (p['id'],))
        nombres = cur.fetchone()
        print(f"  ✅ Pareja {p['id']}: {nombres['j1']} / {nombres['j2']}")
else:
    print(f"  - No hay parejas con jugador1_id = {id_temp}")

# 2. Actualizar torneos_parejas (jugador2_id)
print(f"\n2️⃣  Actualizar torneos_parejas (jugador2_id)")
cur.execute("""
    UPDATE torneos_parejas
    SET jugador2_id = %s
    WHERE jugador2_id = %s
    RETURNING id, jugador1_id, jugador2_id
""", (id_real, id_temp))

parejas_j2 = cur.fetchall()
if parejas_j2:
    for p in parejas_j2:
        # Obtener nombres
        cur.execute("""
            SELECT 
                pu1.nombre || ' ' || pu1.apellido as j1,
                pu2.nombre || ' ' || pu2.apellido as j2
            FROM torneos_parejas tp
            JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tp.id = %s
        """, (p['id'],))
        nombres = cur.fetchone()
        print(f"  ✅ Pareja {p['id']}: {nombres['j1']} / {nombres['j2']}")
else:
    print(f"  - No hay parejas con jugador2_id = {id_temp}")

# 3. Actualizar historial_rating
print(f"\n3️⃣  Actualizar historial_rating")
cur.execute("""
    UPDATE historial_rating
    SET id_usuario = %s
    WHERE id_usuario = %s
    RETURNING id_historial
""", (id_real, id_temp))

historiales = cur.fetchall()
if historiales:
    print(f"  ✅ {len(historiales)} registros actualizados")
else:
    print(f"  - No hay historial para usuario {id_temp}")

conn.commit()

print("\n" + "=" * 80)
print("✅ MIGRACIÓN COMPLETADA")
print("=" * 80)

print(f"\nMauricio Macia (ID {id_real}) ahora tiene todas las parejas y partidos del temp {id_temp}")

# Verificar parejas finales
cur.execute("""
    SELECT 
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE (tp.jugador1_id = %s OR tp.jugador2_id = %s)
    AND tp.torneo_id = 46
""", (id_real, id_real))

parejas_final = cur.fetchall()

print(f"\nParejas de Mauricio Macia (ID {id_real}) en T46:")
for p in parejas_final:
    print(f"  - Pareja {p['id']}: {p['j1']} / {p['j2']}")

cur.close()
conn.close()
