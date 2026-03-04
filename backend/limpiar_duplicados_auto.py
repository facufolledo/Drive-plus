"""
Limpiar duplicados en historial_rating automáticamente
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Buscar duplicados
cur.execute("""
    SELECT id_usuario, id_partido, COUNT(*) as cantidad
    FROM historial_rating
    GROUP BY id_usuario, id_partido
    HAVING COUNT(*) > 1
""")

duplicados = cur.fetchall()

print(f"🔍 Encontrados {len(duplicados)} casos de duplicados\n")

if duplicados:
    for user_id, partido_id, cantidad in duplicados:
        print(f"   Usuario {user_id}, Partido {partido_id}: {cantidad} registros")
    
    print(f"\n🗑️  Eliminando duplicados (manteniendo el primer registro)...")
    
    # Eliminar duplicados manteniendo el de menor id
    cur.execute("""
        DELETE FROM historial_rating
        WHERE id_historial IN (
            SELECT id_historial
            FROM (
                SELECT id_historial,
                       ROW_NUMBER() OVER (PARTITION BY id_usuario, id_partido ORDER BY id_historial) as rn
                FROM historial_rating
            ) t
            WHERE rn > 1
        )
    """)
    
    eliminados = cur.rowcount
    conn.commit()
    print(f"✅ {eliminados} registros duplicados eliminados\n")
    
    # Verificar
    cur.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT id_usuario, id_partido, COUNT(*) as cantidad
            FROM historial_rating
            GROUP BY id_usuario, id_partido
            HAVING COUNT(*) > 1
        ) t
    """)
    
    restantes = cur.fetchone()[0]
    if restantes == 0:
        print("✅ No quedan duplicados en historial_rating")
    else:
        print(f"⚠️  Aún quedan {restantes} duplicados")
else:
    print("✅ No hay duplicados")

cur.close()
conn.close()
