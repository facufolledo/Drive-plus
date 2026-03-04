"""
Script para verificar la estructura de partidos en producción
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno de PRODUCCIÓN
load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL no encontrada en .env.production")
    sys.exit(1)

print(f"🔗 Conectando a: {DATABASE_URL[:50]}...")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Verificar partidos en tabla partidos
    query1 = text("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN estado = 'completado' THEN 1 END) as completados
        FROM partidos
    """)
    result1 = session.execute(query1).fetchone()
    print(f"\n📊 Partidos totales: {result1[0]}")
    print(f"📊 Partidos completados: {result1[1]}")
    
    # Verificar resultados_partidos
    query2 = text("""
        SELECT COUNT(*) as total
        FROM resultados_partidos
    """)
    result2 = session.execute(query2).fetchone()
    print(f"📊 Resultados de partidos: {result2[0]}")
    
    # Ver algunos partidos completados con sus jugadores
    query3 = text("""
        SELECT p.id_partido, p.categoria, p.estado, p.fecha,
               rp.id_pareja_ganadora, rp.id_pareja_perdedora
        FROM partidos p
        LEFT JOIN resultados_partidos rp ON p.id_partido = rp.id_partido
        WHERE p.estado = 'completado'
        ORDER BY p.fecha DESC
        LIMIT 10
    """)
    partidos = session.execute(query3).fetchall()
    
    print(f"\n{'='*100}")
    print(f"Últimos 10 partidos completados:")
    print(f"{'='*100}")
    print(f"{'ID':<8} {'Categoría':<15} {'Estado':<12} {'Fecha':<20} {'Ganadora':<10} {'Perdedora':<10}")
    print(f"{'-'*100}")
    for partido in partidos:
        print(f"{partido[0]:<8} {partido[1]:<15} {partido[2]:<12} {str(partido[3]):<20} {partido[4] or 'N/A':<10} {partido[5] or 'N/A':<10}")
    
    # Ver parejas y sus jugadores
    query4 = text("""
        SELECT COUNT(*) as total
        FROM parejas
    """)
    result4 = session.execute(query4).fetchone()
    print(f"\n📊 Parejas totales: {result4[0]}")
    
    # Ver usuarios en parejas
    query5 = text("""
        SELECT COUNT(DISTINCT id_usuario1) + COUNT(DISTINCT id_usuario2) as total_usuarios
        FROM parejas
    """)
    result5 = session.execute(query5).fetchone()
    print(f"📊 Usuarios en parejas: {result5[0]}")
    
    # Ver historial_rating con más detalle
    query6 = text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.rating,
               COUNT(hr.id_historial) as cambios_rating,
               SUM(hr.delta) as suma_deltas
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN historial_rating hr ON u.id_usuario = hr.id_usuario
        GROUP BY u.id_usuario, p.nombre, p.apellido, u.rating
        ORDER BY cambios_rating DESC
        LIMIT 10
    """)
    usuarios_rating = session.execute(query6).fetchall()
    
    print(f"\n{'='*100}")
    print(f"Top 10 usuarios con más cambios de rating:")
    print(f"{'='*100}")
    print(f"{'ID':<6} {'Nombre':<30} {'Rating':<8} {'Cambios':<8} {'Suma Deltas':<12}")
    print(f"{'-'*100}")
    for user_id, nombre, apellido, rating, cambios, suma in usuarios_rating:
        print(f"{user_id:<6} {nombre} {apellido:<30} {rating:<8} {cambios:<8} {suma or 0:<12}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
