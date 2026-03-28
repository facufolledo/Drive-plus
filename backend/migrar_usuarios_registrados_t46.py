import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("MIGRAR USUARIOS REGISTRADOS - TORNEO 46")
print("=" * 80)

# Migraciones a realizar:
# 1. Dario Barrionuevo: 175 (viejo) → 1105 (nuevo registrado)
# 2. Pablo Toledo: 1102 (temp) → 1104 (registrado)
# 3. Lautaro Macia: 1154 (temp "Mauri") → 1162 (registrado)

migraciones = [
    {
        "nombre": "Dario Barrionuevo",
        "id_viejo": 175,
        "id_nuevo": 1105,
        "razon": "Usuario viejo con email @driveplus.temp → cuenta registrada real"
    },
    {
        "nombre": "Pablo Toledo",
        "id_viejo": 1102,
        "id_nuevo": 1104,
        "razon": "Temp → cuenta registrada"
    },
    {
        "nombre": "Lautaro Macia",
        "id_viejo": 1154,
        "id_nuevo": 1162,
        "razon": "Temp 'Mauri Macia' → cuenta registrada 'Lautaro Macia'"
    }
]

for mig in migraciones:
    print(f"\n{'=' * 80}")
    print(f"MIGRAR: {mig['nombre']}")
    print(f"  {mig['id_viejo']} → {mig['id_nuevo']}")
    print(f"  Razón: {mig['razon']}")
    print("=" * 80)
    
    id_viejo = mig['id_viejo']
    id_nuevo = mig['id_nuevo']
    
    # 1. Actualizar torneos_parejas (jugador1_id)
    print(f"\n1️⃣  Actualizar torneos_parejas (jugador1_id)")
    cur.execute("""
        UPDATE torneos_parejas
        SET jugador1_id = %s
        WHERE jugador1_id = %s
        AND torneo_id = 46
        RETURNING id, jugador1_id, jugador2_id
    """, (id_nuevo, id_viejo))
    
    parejas_j1 = cur.fetchall()
    if parejas_j1:
        for p in parejas_j1:
            print(f"  ✅ Pareja {p['id']}: jugador1_id actualizado a {p['jugador1_id']}")
    else:
        print(f"  - No hay parejas con jugador1_id = {id_viejo}")
    
    # 2. Actualizar torneos_parejas (jugador2_id)
    print(f"\n2️⃣  Actualizar torneos_parejas (jugador2_id)")
    cur.execute("""
        UPDATE torneos_parejas
        SET jugador2_id = %s
        WHERE jugador2_id = %s
        AND torneo_id = 46
        RETURNING id, jugador1_id, jugador2_id
    """, (id_nuevo, id_viejo))
    
    parejas_j2 = cur.fetchall()
    if parejas_j2:
        for p in parejas_j2:
            print(f"  ✅ Pareja {p['id']}: jugador2_id actualizado a {p['jugador2_id']}")
    else:
        print(f"  - No hay parejas con jugador2_id = {id_viejo}")
    
    # 3. Actualizar historial_rating
    print(f"\n3️⃣  Actualizar historial_rating")
    cur.execute("""
        UPDATE historial_rating
        SET id_usuario = %s
        WHERE id_usuario = %s
        RETURNING id_historial, id_usuario, rating_despues
    """, (id_nuevo, id_viejo))
    
    historiales = cur.fetchall()
    if historiales:
        print(f"  ✅ {len(historiales)} registros actualizados")
        for h in historiales[:3]:
            print(f"    - Historial {h['id_historial']}: rating {h['rating_despues']}")
        if len(historiales) > 3:
            print(f"    ... y {len(historiales) - 3} más")
    else:
        print(f"  - No hay historial para usuario {id_viejo}")
    
    # 4. Verificar si el usuario viejo tiene otras referencias
    print(f"\n4️⃣  Verificar otras referencias")
    
    # Salas
    cur.execute("""
        SELECT COUNT(*) as total FROM salas WHERE id_creador = %s
    """, (id_viejo,))
    salas = cur.fetchone()['total']
    if salas > 0:
        print(f"  ⚠️  Usuario {id_viejo} tiene {salas} salas creadas")
    
    # Partidos creados
    cur.execute("""
        SELECT COUNT(*) as total FROM partidos WHERE id_creador = %s
    """, (id_viejo,))
    partidos = cur.fetchone()['total']
    if partidos > 0:
        print(f"  ⚠️  Usuario {id_viejo} tiene {partidos} partidos creados")
    
    if salas == 0 and partidos == 0:
        print(f"  ✓ No hay otras referencias")

conn.commit()

print("\n" + "=" * 80)
print("RESUMEN DE MIGRACIONES")
print("=" * 80)

for mig in migraciones:
    print(f"\n✅ {mig['nombre']}: {mig['id_viejo']} → {mig['id_nuevo']}")

print("\n⚠️  NOTA: Los usuarios viejos/temp NO se eliminan automáticamente.")
print("   Revisa el output para ver si tienen otras referencias antes de eliminar.")

cur.close()
conn.close()
