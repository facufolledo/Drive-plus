"""
Verificar deltas de Dario Barrionuevo
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Buscar Dario
cur.execute("""
    SELECT u.id_usuario, p.nombre, p.apellido, u.rating
    FROM usuarios u
    JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
    WHERE p.nombre ILIKE 'Dario' AND p.apellido ILIKE 'Barrionuevo'
""")

usuario = cur.fetchone()
if usuario:
    user_id, nombre, apellido, rating = usuario
    print(f"Usuario: {nombre} {apellido} (ID: {user_id})")
    print(f"Rating actual: {rating}\n")
    
    # Ver historial
    cur.execute("""
        SELECT h.id_partido, h.delta, h.rating_antes, h.rating_despues, p.fecha
        FROM historial_rating h
        JOIN partidos p ON h.id_partido = p.id_partido
        WHERE h.id_usuario = %s
        ORDER BY p.fecha ASC
    """, (user_id,))
    
    historial = cur.fetchall()
    print(f"Historial ({len(historial)} registros):")
    print(f"{'Partido':<10} {'Delta':>7} {'Antes':>7} {'Después':>9}")
    print("-" * 50)
    
    suma = 0
    for id_partido, delta, antes, despues, fecha in historial:
        print(f"{id_partido:<10} {delta:>+7} {antes:>7} {despues:>9}")
        suma += delta
    
    print("-" * 50)
    print(f"Suma total de deltas: {suma:+d}")
    print(f"Rating esperado (249 + {suma:+d}): {249 + suma}")
    print(f"Rating actual: {rating}")
    print(f"Diferencia: {rating - (249 + suma):+d}")

cur.close()
conn.close()
