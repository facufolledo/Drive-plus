"""
Corregir Juan Loto - registrado como Principiante pero es 5ta
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Buscar Juan Loto
cur.execute("""
    SELECT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria, c.nombre as cat_actual
    FROM usuarios u
    JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
    LEFT JOIN categorias c ON u.id_categoria = c.id_categoria
    WHERE p.nombre ILIKE 'Juan' AND p.apellido ILIKE 'Loto'
""")

usuario = cur.fetchone()
if not usuario:
    print("❌ Usuario no encontrado")
    cur.close()
    conn.close()
    exit()

user_id, nombre, apellido, rating_actual, id_cat_actual, cat_actual = usuario

print(f"👤 Usuario: {nombre} {apellido} (ID: {user_id})")
print(f"📊 Rating actual: {rating_actual}")
print(f"🎯 Categoría actual: {cat_actual}\n")

# Ver historial de partidos
cur.execute("""
    SELECT h.id_partido, h.delta, h.rating_antes, h.rating_despues
    FROM historial_rating h
    JOIN partidos p ON h.id_partido = p.id_partido
    WHERE h.id_usuario = %s
    ORDER BY p.fecha ASC
""", (user_id,))

partidos = cur.fetchall()

print(f"📈 Historial ({len(partidos)} partidos):")
print(f"{'Partido':<10} {'Delta':>7} {'Antes':>7} {'Después':>9}")
print("-" * 50)

suma_deltas = 0
for id_partido, delta, antes, despues in partidos:
    print(f"{id_partido:<10} {delta:>+7} {antes:>7} {despues:>9}")
    suma_deltas += delta

print("-" * 50)
print(f"Suma de deltas: {suma_deltas:+d}\n")

# Obtener ID de categoría 5ta
cur.execute("SELECT id_categoria FROM categorias WHERE nombre = '5ta'")
id_5ta = cur.fetchone()[0]

rating_inicial_5ta = 1499
rating_esperado = rating_inicial_5ta + suma_deltas

print(f"{'='*50}")
print(f"CORRECCIÓN:")
print(f"  Categoría: {cat_actual} → 5ta")
print(f"  Rating inicial: 249 → 1499")
print(f"  Suma deltas: {suma_deltas:+d}")
print(f"  Rating esperado: {rating_esperado}")
print(f"  Rating actual: {rating_actual}")
print(f"{'='*50}\n")

respuesta = input("¿Aplicar corrección? (s/n): ")

if respuesta.lower() == 's':
    # Actualizar categoría y rating en usuarios
    cur.execute("""
        UPDATE usuarios
        SET id_categoria = %s, rating = %s
        WHERE id_usuario = %s
    """, (id_5ta, rating_esperado, user_id))
    
    # Actualizar id_categoria_inicial en perfil_usuarios
    cur.execute("""
        UPDATE perfil_usuarios
        SET id_categoria_inicial = %s
        WHERE id_usuario = %s
    """, (id_5ta, user_id))
    
    conn.commit()
    print(f"\n✅ Juan Loto corregido:")
    print(f"   Categoría: 5ta")
    print(f"   Rating: {rating_esperado}")
else:
    print("\n❌ Cancelado")

cur.close()
conn.close()
