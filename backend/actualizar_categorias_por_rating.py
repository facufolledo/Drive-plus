"""
Actualizar categorías de todos los usuarios según su rating
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')

# Rangos de categorías ACTUALES (para asignar categoría según rating)
RANGOS = [
    ('Principiante', 0, 499),
    ('8va', 500, 999),
    ('7ma', 1000, 1199),
    ('6ta', 1200, 1399),
    ('5ta', 1400, 1599),
    ('4ta', 1600, 1799),
    ('3ra', 1800, 9999)
]

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Obtener IDs de categorías
cur.execute("SELECT id_categoria, nombre FROM categorias")
categorias_map = {nombre: id_cat for id_cat, nombre in cur.fetchall()}

# Obtener todos los usuarios con rating
cur.execute("""
    SELECT u.id_usuario, p.nombre, p.apellido, u.rating, c.nombre as cat_actual
    FROM usuarios u
    JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
    LEFT JOIN categorias c ON u.id_categoria = c.id_categoria
    WHERE p.nombre NOT LIKE '%temp%'
    AND p.apellido NOT LIKE '%temp%'
    ORDER BY u.rating DESC
""")

usuarios = cur.fetchall()

print(f"\n🔍 Verificando {len(usuarios)} usuarios...\n")

usuarios_a_actualizar = []

for user_id, nombre, apellido, rating, cat_actual in usuarios:
    # Determinar categoría correcta según rating
    cat_correcta = None
    for cat_nombre, min_rating, max_rating in RANGOS:
        if min_rating <= rating <= max_rating:
            cat_correcta = cat_nombre
            break
    
    if cat_correcta and cat_correcta != cat_actual:
        usuarios_a_actualizar.append({
            'user_id': user_id,
            'nombre': f"{nombre} {apellido}",
            'rating': rating,
            'cat_actual': cat_actual,
            'cat_correcta': cat_correcta,
            'id_cat_correcta': categorias_map[cat_correcta]
        })

print(f"{'='*90}")
print(f"\n📊 RESUMEN:")
print(f"   Total usuarios: {len(usuarios)}")
print(f"   ⚠️  Con categoría incorrecta: {len(usuarios_a_actualizar)}")
print(f"   ✓  Con categoría correcta: {len(usuarios) - len(usuarios_a_actualizar)}\n")

if usuarios_a_actualizar:
    print(f"{'='*90}")
    print(f"USUARIOS CON CATEGORÍA INCORRECTA ({len(usuarios_a_actualizar)}):")
    print(f"{'='*90}")
    print(f"{'Nombre':<30} {'Rating':>7} {'Actual':<16} {'Correcta':<16}")
    print(f"{'-'*90}")
    for u in usuarios_a_actualizar:
        print(f"{u['nombre']:<30} {u['rating']:>7} {u['cat_actual']:<16} {u['cat_correcta']:<16}")
    
    print(f"\n{'='*90}")
    respuesta = input(f"¿Actualizar las {len(usuarios_a_actualizar)} categorías? (s/n): ")
    
    if respuesta.lower() == 's':
        for u in usuarios_a_actualizar:
            cur.execute("""
                UPDATE usuarios
                SET id_categoria = %s
                WHERE id_usuario = %s
            """, (u['id_cat_correcta'], u['user_id']))
            print(f"✅ {u['nombre']}: {u['cat_actual']} → {u['cat_correcta']}")
        
        conn.commit()
        print(f"\n✅ {len(usuarios_a_actualizar)} categorías actualizadas")
    else:
        print("\n❌ Cancelado")
else:
    print("✅ Todas las categorías están correctas")

cur.close()
conn.close()
