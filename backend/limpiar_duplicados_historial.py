"""
Detectar y limpiar duplicados en historial_rating
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Buscar duplicados (mismo usuario + mismo partido)
cur.execute("""
    SELECT id_usuario, id_partido, COUNT(*) as cantidad
    FROM historial_rating
    GROUP BY id_usuario, id_partido
    HAVING COUNT(*) > 1
    ORDER BY cantidad DESC
""")

duplicados = cur.fetchall()

print(f"🔍 Encontrados {len(duplicados)} casos de duplicados en historial_rating\n")

if duplicados:
    print(f"{'Usuario':<10} {'Partido':<10} {'Cantidad':<10}")
    print("-" * 40)
    for user_id, partido_id, cantidad in duplicados[:20]:  # Mostrar primeros 20
        print(f"{user_id:<10} {partido_id:<10} {cantidad:<10}")
    
    if len(duplicados) > 20:
        print(f"... y {len(duplicados) - 20} más")
    
    print(f"\n{'='*80}")
    print("SOLUCIÓN: Eliminar duplicados manteniendo solo el primer registro")
    print(f"{'='*80}")
    
    respuesta = input(f"\n¿Eliminar {len(duplicados)} duplicados en PRODUCCIÓN? (s/n): ")
    
    if respuesta.lower() == 's':
        # Eliminar duplicados manteniendo el de menor id (el primero insertado)
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
        print(f"\n✅ {eliminados} registros duplicados eliminados")
        
        # Verificar que no queden duplicados
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
        print("\n❌ Operación cancelada")
else:
    print("✅ No hay duplicados en historial_rating")

cur.close()
conn.close()
