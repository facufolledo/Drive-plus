import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("FIX PAREJAS ZONA E - CATEGORÍA ASIGNADA")
print("=" * 80)

# Obtener las 3 parejas de los partidos de Zona E (ID 426)
cur.execute("""
    SELECT DISTINCT tp.id, tp.categoria_id, tp.categoria_asignada
    FROM torneos_parejas tp
    JOIN partidos p ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
    WHERE p.zona_id = 426
    ORDER BY tp.id
""")

parejas = cur.fetchall()

print(f"\nParejas en Zona E (426):")
for p in parejas:
    print(f"  Pareja {p['id']}: categoria_id={p['categoria_id']}, categoria_asignada={p['categoria_asignada']}")

# Actualizar categoria_asignada si es NULL
print("\n" + "=" * 80)
print("ACTUALIZAR CATEGORIA_ASIGNADA")
print("=" * 80)

for p in parejas:
    if not p['categoria_asignada']:
        cur.execute("""
            UPDATE torneos_parejas
            SET categoria_asignada = %s
            WHERE id = %s
        """, (p['categoria_id'], p['id']))
        print(f"✅ Pareja {p['id']}: categoria_asignada actualizada a {p['categoria_id']}")
    else:
        print(f"✓ Pareja {p['id']}: ya tiene categoria_asignada = {p['categoria_asignada']}")

# Verificar estado de las parejas
print("\n" + "=" * 80)
print("VERIFICAR ESTADO DE PAREJAS")
print("=" * 80)

cur.execute("""
    SELECT 
        tp.id,
        tp.estado,
        tp.pago_estado,
        tp.confirmado_jugador1,
        tp.confirmado_jugador2,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    JOIN partidos p ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
    WHERE p.zona_id = 426
    GROUP BY tp.id, tp.estado, tp.pago_estado, tp.confirmado_jugador1, tp.confirmado_jugador2, pu1.nombre, pu1.apellido, pu2.nombre, pu2.apellido
    ORDER BY tp.id
""")

parejas_estado = cur.fetchall()

for p in parejas_estado:
    print(f"\nPareja {p['id']}: {p['j1']} / {p['j2']}")
    print(f"  Estado: {p['estado']}")
    print(f"  Pago: {p['pago_estado']}")
    print(f"  Confirmado J1: {p['confirmado_jugador1']}")
    print(f"  Confirmado J2: {p['confirmado_jugador2']}")
    
    # Actualizar si es necesario
    if p['estado'] != 'confirmada':
        cur.execute("""
            UPDATE torneos_parejas
            SET estado = 'confirmada'
            WHERE id = %s
        """, (p['id'],))
        print(f"  ✅ Estado actualizado a 'confirmada'")
    
    if p['pago_estado'] != 'aprobado':
        cur.execute("""
            UPDATE torneos_parejas
            SET pago_estado = 'aprobado'
            WHERE id = %s
        """, (p['id'],))
        print(f"  ✅ Pago actualizado a 'aprobado'")

conn.commit()

# Verificación final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL")
print("=" * 80)

cur.execute("""
    SELECT 
        tp.id,
        tp.categoria_id,
        tp.categoria_asignada,
        tp.estado,
        tp.pago_estado,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    JOIN partidos p ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
    WHERE p.zona_id = 426
    GROUP BY tp.id, tp.categoria_id, tp.categoria_asignada, tp.estado, tp.pago_estado, pu1.nombre, pu1.apellido, pu2.nombre, pu2.apellido
    ORDER BY tp.id
""")

parejas_final = cur.fetchall()

for p in parejas_final:
    print(f"\n✅ Pareja {p['id']}: {p['j1']} / {p['j2']}")
    print(f"   Categoría: {p['categoria_id']} | Asignada: {p['categoria_asignada']}")
    print(f"   Estado: {p['estado']} | Pago: {p['pago_estado']}")

print("\n" + "=" * 80)
print("✅ PAREJAS ACTUALIZADAS")
print("=" * 80)

cur.close()
conn.close()
