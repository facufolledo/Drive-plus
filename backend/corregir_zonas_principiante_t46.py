import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CORREGIR ZONAS PRINCIPIANTE - TORNEO 46")
print("=" * 80)
print("\nREQUERIMIENTO:")
print("  Ludueña/Apostolo (P1048) + Aballay/Ríos (P1042) + Jatuff/Alcazar (P1041)")
print("  deben estar en la MISMA ZONA")

# Obtener zonas actuales
cur.execute("""
    SELECT 
        tz.id as zona_id,
        tz.nombre as zona,
        p.id_partido,
        p.pareja1_id,
        p.pareja2_id
    FROM partidos p
    JOIN torneo_zonas tz ON p.zona_id = tz.id
    WHERE p.id_torneo = 46
    AND p.categoria_id = 125
    AND p.fase = 'zona'
    ORDER BY tz.nombre, p.id_partido
""")

partidos_actuales = cur.fetchall()

print("\n📊 DISTRIBUCIÓN ACTUAL:")
zona_actual = None
for p in partidos_actuales:
    if p['zona'] != zona_actual:
        zona_actual = p['zona']
        print(f"\n{zona_actual} (ID: {p['zona_id']})")
    print(f"  Partido {p['id_partido']}: P{p['pareja1_id']} vs P{p['pareja2_id']}")

# Identificar las zonas
# Zona A tiene P1049, P1050, P1041 (Jatuff/Alcazar)
# Zona B tiene P1042 (Aballay/Ríos), P1048 (Ludueña/Apostolo), P1052

# Necesitamos mover P1041 de Zona A a Zona B
# Y mover P1049 y P1050 a otra zona (Zona C o D)

print("\n" + "=" * 80)
print("SOLUCIÓN:")
print("=" * 80)
print("1. Mover P1041 (Jatuff/Alcazar) de Zona A → Zona B")
print("2. Mover P1049 (Agostini/Paez) de Zona A → Zona C")
print("3. Mover P1050 (Villalba/Alvarado) de Zona A → Zona D")

try:
    # Obtener IDs de zonas
    cur.execute("""
        SELECT id, nombre
        FROM torneo_zonas
        WHERE torneo_id = 46
        AND categoria_id = 125
        ORDER BY nombre
    """)
    
    zonas = {z['nombre']: z['id'] for z in cur.fetchall()}
    
    zona_a_id = zonas['Zona A']
    zona_b_id = zonas['Zona B']
    zona_c_id = zonas['Zona C']
    zona_d_id = zonas['Zona D']
    
    # Eliminar partidos actuales de Zona A
    cur.execute("""
        DELETE FROM partidos
        WHERE zona_id = %s
        AND id_torneo = 46
        AND categoria_id = 125
        AND fase = 'zona'
    """, (zona_a_id,))
    
    print(f"\n✅ Partidos de Zona A eliminados")
    
    # Crear nuevos partidos para Zona A: P1049, P1050, P1052 (mover P1052 de Zona B)
    # Primero eliminar P1052 de Zona B
    cur.execute("""
        DELETE FROM partidos
        WHERE zona_id = %s
        AND (pareja1_id = 1052 OR pareja2_id = 1052)
        AND id_torneo = 46
        AND categoria_id = 125
        AND fase = 'zona'
    """, (zona_b_id,))
    
    # Crear partidos Zona A: P1049 vs P1050, P1049 vs P1052, P1050 vs P1052
    partidos_zona_a = [
        (1049, 1050),
        (1049, 1052),
        (1050, 1052)
    ]
    
    for p1, p2 in partidos_zona_a:
        cur.execute("""
            INSERT INTO partidos (
                id_torneo, categoria_id, fase, zona_id,
                pareja1_id, pareja2_id
            )
            VALUES (46, 125, 'zona', %s, %s, %s)
        """, (zona_a_id, p1, p2))
    
    print(f"✅ Zona A: P1049, P1050, P1052")
    
    # Crear partidos Zona B: P1041, P1042, P1048
    partidos_zona_b = [
        (1041, 1042),
        (1041, 1048),
        (1042, 1048)
    ]
    
    for p1, p2 in partidos_zona_b:
        cur.execute("""
            INSERT INTO partidos (
                id_torneo, categoria_id, fase, zona_id,
                pareja1_id, pareja2_id
            )
            VALUES (46, 125, 'zona', %s, %s, %s)
        """, (zona_b_id, p1, p2))
    
    print(f"✅ Zona B: P1041 (Jatuff/Alcazar), P1042 (Aballay/Ríos), P1048 (Ludueña/Apostolo)")
    
    conn.commit()
    
    print("\n" + "=" * 80)
    print("✅ ZONAS CORREGIDAS - AHORA REGENERAR FIXTURE")
    print("=" * 80)
    print("\nNOTA: Los partidos se crearon sin horarios.")
    print("Ejecuta: generar_fixture_principiante_service_t46.py")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
