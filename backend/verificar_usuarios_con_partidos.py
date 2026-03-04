"""
Script para verificar cuántos usuarios tienen partidos en producción
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
    # Contar usuarios con partidos en partido_jugadores
    query1 = text("""
        SELECT COUNT(DISTINCT id_usuario) as total
        FROM partido_jugadores
    """)
    result1 = session.execute(query1).fetchone()
    print(f"\n📊 Usuarios en partido_jugadores: {result1[0]}")
    
    # Contar usuarios con partidos completados
    query2 = text("""
        SELECT COUNT(DISTINCT pj.id_usuario) as total
        FROM partido_jugadores pj
        JOIN partidos p ON pj.id_partido = p.id_partido
        WHERE p.estado = 'completado'
    """)
    result2 = session.execute(query2).fetchone()
    print(f"📊 Usuarios con partidos completados: {result2[0]}")
    
    # Contar usuarios con historial_rating
    query3 = text("""
        SELECT COUNT(DISTINCT id_usuario) as total
        FROM historial_rating
    """)
    result3 = session.execute(query3).fetchone()
    print(f"📊 Usuarios en historial_rating: {result3[0]}")
    
    # Listar algunos usuarios con partidos
    query4 = text("""
        SELECT DISTINCT u.id_usuario, p.nombre, p.apellido, u.rating,
               (SELECT COUNT(*) FROM partido_jugadores pj2 WHERE pj2.id_usuario = u.id_usuario) as num_partidos
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN partido_jugadores pj ON u.id_usuario = pj.id_usuario
        ORDER BY num_partidos DESC
        LIMIT 20
    """)
    usuarios = session.execute(query4).fetchall()
    
    print(f"\n{'='*80}")
    print(f"Top 20 usuarios con más partidos:")
    print(f"{'='*80}")
    print(f"{'ID':<6} {'Nombre':<30} {'Rating':>6} {'Partidos':>8}")
    print(f"{'-'*80}")
    for user_id, nombre, apellido, rating, num_partidos in usuarios:
        print(f"{user_id:<6} {nombre} {apellido:<30} {rating:>6} {num_partidos:>8}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
