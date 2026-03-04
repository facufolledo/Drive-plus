"""
Verificar Kevin Gurgone
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Buscar Kevin
cur.execute("""
    SELECT 
        u.id_usuario, 
        p.nombre, 
        p.apellido, 
        u.rating,
        c_actual.nombre as cat_actual,
        c_inicial.nombre as cat_inicial,
        pu.id_categoria_inicial
    FROM usuarios u
    JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
    LEFT JOIN categorias c_actual ON u.id_categoria = c_actual.id_categoria
    LEFT JOIN categorias c_inicial ON pu.id_categoria_inicial = c_inicial.id_categoria
    WHERE p.nombre ILIKE 'Kevin' AND p.apellido ILIKE 'Gurgone'
""")

usuario = cur.fetchone()
if usuario:
    user_id, nombre, apellido, rating, cat_actual, cat_inicial, id_cat_inicial = usuario
    print(f"Usuario: {nombre} {apellido} (ID: {user_id})")
    print(f"Rating actual: {rating}")
    print(f"Categoría actual: {cat_actual}")
    print(f"Categoría inicial (id): {id_cat_inicial}")
    print(f"Categoría inicial (nombre): {cat_inicial}")
    print()
    
    # Ver primer partido
    cur.execute("""
        SELECT h.rating_antes, p.fecha
        FROM historial_rating h
        JOIN partidos p ON h.id_partido = p.id_partido
        WHERE h.id_usuario = %s
        ORDER BY p.fecha ASC
        LIMIT 1
    """, (user_id,))
    
    primer = cur.fetchone()
    if primer:
        print(f"Primer partido:")
        print(f"  Rating antes: {primer[0]}")
        print(f"  Fecha: {primer[1]}")

cur.close()
conn.close()
