import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR TABLA torneo_zona_parejas - TORNEO 46")
print("=" * 80)

# Verificar Zona A (que funciona)
print("\n🔹 ZONA A - PRINCIPIANTE (FUNCIONA)")
print("-" * 80)

cur.execute("""
    SELECT tz.id, tz.nombre
    FROM torneo_zonas tz
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 125
    AND tz.nombre = 'Zona A'
""")

zona_a = cur.fetchone()
print(f"Zona A ID: {zona_a['id']}")

cur.execute("""
    SELECT tzp.*, tp.id as pareja_id_real
    FROM torneo_zona_parejas tzp
    JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
    WHERE tzp.zona_id = %s
    ORDER BY tzp.pareja_id
""", (zona_a['id'],))

parejas_a = cur.fetchall()
print(f"Parejas en torneo_zona_parejas: {len(parejas_a)}")
for p in parejas_a:
    print(f"  Pareja {p['pareja_id']} → Zona {p['zona_id']}")

# Verificar Zona E (que NO funciona)
print("\n" + "=" * 80)
print("🔹 ZONA E - PRINCIPIANTE (NO FUNCIONA)")
print("-" * 80)

print(f"Zona E ID: 426")

cur.execute("""
    SELECT tzp.*, tp.id as pareja_id_real
    FROM torneo_zona_parejas tzp
    JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
    WHERE tzp.zona_id = 426
    ORDER BY tzp.pareja_id
""")

parejas_e = cur.fetchall()
print(f"Parejas en torneo_zona_parejas: {len(parejas_e)}")

if parejas_e:
    for p in parejas_e:
        print(f"  Pareja {p['pareja_id']} → Zona {p['zona_id']}")
else:
    print("  ⚠️  NO HAY PAREJAS EN torneo_zona_parejas")
    print("\n  🔧 SOLUCIÓN: Insertar las 3 parejas en torneo_zona_parejas")
    
    # Obtener las parejas de Zona E
    cur.execute("""
        SELECT DISTINCT tp.id
        FROM torneos_parejas tp
        JOIN partidos p ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
        WHERE p.zona_id = 426
        ORDER BY tp.id
    """)
    
    parejas_zona_e = cur.fetchall()
    print(f"\n  Parejas a insertar:")
    for p in parejas_zona_e:
        print(f"    Pareja {p['id']}")
    
    # Insertar
    print("\n  Insertando...")
    for p in parejas_zona_e:
        cur.execute("""
            INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (426, p['id']))
        print(f"    ✅ Pareja {p['id']} insertada en Zona 426")
    
    conn.commit()
    
    # Verificar
    cur.execute("""
        SELECT COUNT(*) as total
        FROM torneo_zona_parejas
        WHERE zona_id = 426
    """)
    
    total = cur.fetchone()['total']
    print(f"\n  ✅ Total parejas en torneo_zona_parejas para Zona E: {total}")

print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL")
print("=" * 80)

cur.execute("""
    SELECT 
        tz.nombre as zona,
        COUNT(DISTINCT tzp.pareja_id) as parejas_en_tabla,
        COUNT(DISTINCT p.id_partido) as partidos
    FROM torneo_zonas tz
    LEFT JOIN torneo_zona_parejas tzp ON tz.id = tzp.zona_id
    LEFT JOIN partidos p ON tz.id = p.zona_id
    WHERE tz.torneo_id = 46
    AND tz.categoria_id = 125
    GROUP BY tz.id, tz.nombre
    ORDER BY tz.nombre
""")

resumen = cur.fetchall()

for r in resumen:
    print(f"\n{r['zona']}: {r['parejas_en_tabla']} parejas en tabla, {r['partidos']} partidos")

cur.close()
conn.close()
