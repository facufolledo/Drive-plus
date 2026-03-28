import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("IDENTIFICAR 7MA EN TORNEO 46")
print("=" * 80)

# Ver una pareja de cada categoría para identificar
for cat_id in [125, 126, 127]:
    print(f"\n{'=' * 80}")
    print(f"CATEGORÍA {cat_id}")
    print("=" * 80)
    
    # Ver zonas
    cur.execute("""
        SELECT id, nombre
        FROM torneo_zonas
        WHERE torneo_id = 46 AND categoria_id = %s
        ORDER BY nombre
        LIMIT 1
    """, (cat_id,))
    
    zona = cur.fetchone()
    
    if zona:
        print(f"\nZona ejemplo: {zona['nombre']} (ID {zona['id']})")
        
        # Ver parejas de esa zona
        cur.execute("""
            SELECT 
                tp.id,
                pu1.nombre || ' ' || pu1.apellido as j1,
                pu2.nombre || ' ' || pu2.apellido as j2
            FROM torneo_zona_parejas tzp
            JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
            JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tzp.zona_id = %s
            LIMIT 2
        """, (zona['id'],))
        
        parejas = cur.fetchall()
        
        print(f"Parejas ejemplo:")
        for p in parejas:
            print(f"  - Pareja {p['id']}: {p['j1']} / {p['j2']}")

print("\n" + "=" * 80)
print("¿Cuál es 7ma?")
print("=" * 80)
print("\nMirando los nombres de las parejas, ¿cuál categoría es 7ma?")
print("  - 125")
print("  - 126")  
print("  - 127")

cur.close()
conn.close()
