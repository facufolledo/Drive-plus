import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno
load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL no encontrada")
    exit(1)

# Crear engine y sesión
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Buscar usuarios con partidos jugados
    result = session.execute(text("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            p.nombre,
            p.apellido,
            u.rating,
            COUNT(DISTINCT hr.id_partido) as partidos_jugados,
            COUNT(CASE WHEN hr.delta > 0 THEN 1 END) as victorias,
            COUNT(CASE WHEN hr.delta < 0 THEN 1 END) as derrotas
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        LEFT JOIN historial_rating hr ON u.id_usuario = hr.id_usuario
        LEFT JOIN partidos pa ON hr.id_partido = pa.id_partido AND pa.estado IN ('finalizado', 'confirmado')
        GROUP BY u.id_usuario, u.nombre_usuario, p.nombre, p.apellido, u.rating
        HAVING COUNT(DISTINCT hr.id_partido) > 0
        ORDER BY u.rating DESC
        LIMIT 10
    """))
    
    usuarios = result.fetchall()
    
    if usuarios:
        print("✅ Usuarios con partidos jugados:\n")
        for u in usuarios:
            winrate = round((u[6] / u[5] * 100) if u[5] > 0 else 0)
            print(f"{u[2]} {u[3]} (@{u[1]})")
            print(f"   Rating: {u[4]}")
            print(f"   Partidos: {u[5]} | Victorias: {u[6]} | Derrotas: {u[7]}")
            print(f"   Winrate: {winrate}%")
            print()
    else:
        print("❌ No hay usuarios con partidos jugados")

finally:
    session.close()
