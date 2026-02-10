"""
Verificar datos en la base de datos para el ranking
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Cargar .env del backend
load_dotenv('backend/.env')

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

print("=" * 60)
print("VERIFICANDO DATOS EN BASE DE DATOS")
print("=" * 60)

with engine.connect() as conn:
    # 1. Verificar tabla historial_rating
    print("\n1. Verificando tabla historial_rating:")
    print("-" * 60)
    
    result = conn.execute(text("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT id_usuario) as usuarios_unicos,
               COUNT(DISTINCT id_partido) as partidos_unicos
        FROM historial_rating
    """))
    row = result.fetchone()
    print(f"Total registros: {row[0]}")
    print(f"Usuarios únicos: {row[1]}")
    print(f"Partidos únicos: {row[2]}")
    
    # 2. Verificar deltas positivos (victorias)
    print("\n2. Verificando deltas (victorias):")
    print("-" * 60)
    
    result = conn.execute(text("""
        SELECT 
            COUNT(*) FILTER (WHERE delta > 0) as deltas_positivos,
            COUNT(*) FILTER (WHERE delta < 0) as deltas_negativos,
            COUNT(*) FILTER (WHERE delta = 0) as deltas_cero
        FROM historial_rating
    """))
    row = result.fetchone()
    print(f"Deltas positivos (victorias): {row[0]}")
    print(f"Deltas negativos (derrotas): {row[1]}")
    print(f"Deltas cero: {row[2]}")
    
    # 3. Verificar estados de partidos
    print("\n3. Verificando estados de partidos:")
    print("-" * 60)
    
    result = conn.execute(text("""
        SELECT estado, COUNT(*) as cantidad
        FROM partidos
        GROUP BY estado
        ORDER BY cantidad DESC
    """))
    for row in result:
        print(f"{row[0]}: {row[1]}")
    
    # 4. Verificar partidos en historial_rating vs partidos tabla
    print("\n4. Verificando relación historial_rating <-> partidos:")
    print("-" * 60)
    
    result = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT hr.id_partido) as partidos_en_historial,
            COUNT(DISTINCT p.id_partido) as partidos_confirmados
        FROM historial_rating hr
        LEFT JOIN partidos p ON hr.id_partido = p.id_partido
        WHERE p.estado IN ('finalizado', 'confirmado')
    """))
    row = result.fetchone()
    print(f"Partidos en historial_rating: {row[0]}")
    print(f"Partidos confirmados/finalizados: {row[1]}")
    
    # 5. Probar la subquery de partidos jugados
    print("\n5. Probando subquery de partidos jugados (primeros 5 usuarios):")
    print("-" * 60)
    
    result = conn.execute(text("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            u.rating,
            COUNT(DISTINCT hr.id_partido) as partidos_jugados,
            COUNT(*) FILTER (WHERE hr.delta > 0) as victorias
        FROM usuarios u
        LEFT JOIN historial_rating hr ON u.id_usuario = hr.id_usuario
        LEFT JOIN partidos p ON hr.id_partido = p.id_partido
        WHERE p.estado IN ('finalizado', 'confirmado')
        GROUP BY u.id_usuario, u.nombre_usuario, u.rating
        HAVING COUNT(DISTINCT hr.id_partido) > 0
        ORDER BY u.rating DESC
        LIMIT 5
    """))
    
    for row in result:
        print(f"{row[1]} (ID: {row[0]}): Rating {row[2]} | {row[3]} partidos | {row[4]} victorias")
    
    # 6. Verificar si hay usuarios con partidos pero sin historial
    print("\n6. Verificando usuarios con campo partidos_jugados > 0:")
    print("-" * 60)
    
    result = conn.execute(text("""
        SELECT id_usuario, nombre_usuario, rating, partidos_jugados
        FROM usuarios
        WHERE partidos_jugados > 0
        ORDER BY rating DESC
        LIMIT 5
    """))
    
    for row in result:
        print(f"{row[1]} (ID: {row[0]}): Rating {row[2]} | partidos_jugados={row[3]}")

print("\n" + "=" * 60)
print("VERIFICACIÓN COMPLETADA")
print("=" * 60)
