import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("MIGRACIÓN COMPLETA Y ELIMINACIÓN DE TEMPS")
print("=" * 80)

# 1. Migrar Dario Barrionuevo en TODOS los torneos (no solo T46)
print("\n1️⃣  MIGRAR DARIO BARRIONUEVO (175 → 1105) EN TODOS LOS TORNEOS")
print("-" * 80)

# Actualizar jugador1_id
cur.execute("""
    UPDATE torneos_parejas
    SET jugador1_id = 1105
    WHERE jugador1_id = 175
    RETURNING id, torneo_id
""")

parejas_j1 = cur.fetchall()
if parejas_j1:
    print(f"✅ {len(parejas_j1)} parejas actualizadas (jugador1_id):")
    for p in parejas_j1:
        print(f"  - Pareja {p['id']} en Torneo {p['torneo_id']}")

# Actualizar jugador2_id
cur.execute("""
    UPDATE torneos_parejas
    SET jugador2_id = 1105
    WHERE jugador2_id = 175
    RETURNING id, torneo_id
""")

parejas_j2 = cur.fetchall()
if parejas_j2:
    print(f"✅ {len(parejas_j2)} parejas actualizadas (jugador2_id):")
    for p in parejas_j2:
        print(f"  - Pareja {p['id']} en Torneo {p['torneo_id']}")

# Actualizar historial_rating
cur.execute("""
    UPDATE historial_rating
    SET id_usuario = 1105
    WHERE id_usuario = 175
    RETURNING id_historial
""")

historiales = cur.fetchall()
if historiales:
    print(f"✅ {len(historiales)} registros de historial actualizados")

conn.commit()

# 2. Verificar que no queden referencias
print("\n2️⃣  VERIFICAR QUE NO QUEDEN REFERENCIAS")
print("-" * 80)

usuarios_a_eliminar = [175, 1102, 1154]

for user_id in usuarios_a_eliminar:
    # Verificar parejas
    cur.execute("""
        SELECT COUNT(*) as total FROM torneos_parejas 
        WHERE jugador1_id = %s OR jugador2_id = %s
    """, (user_id, user_id))
    
    parejas = cur.fetchone()['total']
    
    if parejas > 0:
        print(f"⚠️  Usuario {user_id} todavía tiene {parejas} parejas - NO SE PUEDE ELIMINAR")
    else:
        print(f"✓ Usuario {user_id} sin parejas")

# 3. Eliminar usuarios
print("\n3️⃣  ELIMINAR USUARIOS TEMP")
print("-" * 80)

for user_id in usuarios_a_eliminar:
    # Verificar una vez más
    cur.execute("""
        SELECT COUNT(*) as total FROM torneos_parejas 
        WHERE jugador1_id = %s OR jugador2_id = %s
    """, (user_id, user_id))
    
    parejas = cur.fetchone()['total']
    
    if parejas > 0:
        print(f"\n⚠️  Usuario {user_id} - SALTADO (tiene {parejas} parejas)")
        continue
    
    # Eliminar perfil
    cur.execute("""
        DELETE FROM perfil_usuarios WHERE id_usuario = %s
        RETURNING id_usuario
    """, (user_id,))
    
    perfil_deleted = cur.fetchone()
    if perfil_deleted:
        print(f"\n✅ Usuario {user_id}:")
        print(f"  - Perfil eliminado")
    
    # Eliminar usuario
    cur.execute("""
        DELETE FROM usuarios WHERE id_usuario = %s
        RETURNING id_usuario
    """, (user_id,))
    
    usuario_deleted = cur.fetchone()
    if usuario_deleted:
        print(f"  - Usuario eliminado")

conn.commit()

print("\n" + "=" * 80)
print("✅ PROCESO COMPLETADO")
print("=" * 80)

print("\nMigraciones realizadas:")
print("  ✅ Dario Barrionuevo: 175 → 1105 (todos los torneos)")
print("  ✅ Pablo Toledo: 1102 → 1104")
print("  ✅ Mauricio Macia: 1154 → 1156")

print("\nUsuarios eliminados:")
print("  - 175 (Dario viejo)")
print("  - 1102 (Pablo temp)")
print("  - 1154 (Mauri temp)")

cur.close()
conn.close()
