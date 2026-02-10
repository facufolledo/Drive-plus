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
    # Verificar deltas en historial_rating
    result = session.execute(text("""
        SELECT 
            COUNT(*) as total_registros,
            COUNT(CASE WHEN delta > 0 THEN 1 END) as deltas_positivos,
            COUNT(CASE WHEN delta < 0 THEN 1 END) as deltas_negativos,
            COUNT(CASE WHEN delta = 0 THEN 1 END) as deltas_cero,
            COUNT(CASE WHEN delta IS NULL THEN 1 END) as deltas_null
        FROM historial_rating hr
        JOIN partidos p ON hr.id_partido = p.id_partido
        WHERE p.estado IN ('finalizado', 'confirmado')
    """))
    
    stats = result.fetchone()
    
    print("📊 Estadísticas de deltas en historial_rating:")
    print(f"   Total registros: {stats[0]}")
    print(f"   Deltas positivos (victorias): {stats[1]}")
    print(f"   Deltas negativos (derrotas): {stats[2]}")
    print(f"   Deltas cero: {stats[3]}")
    print(f"   Deltas NULL: {stats[4]}")
    
    if stats[1] == 0:
        print("\n⚠️  NO HAY DELTAS POSITIVOS - Las victorias no se están contando")
        print("   Esto explica por qué todos tienen 0 victorias")
    
    # Ver algunos ejemplos
    print("\n📋 Ejemplos de registros:")
    result = session.execute(text("""
        SELECT 
            hr.id_usuario,
            hr.id_partido,
            hr.rating_antes,
            hr.rating_despues,
            hr.delta,
            p.estado
        FROM historial_rating hr
        JOIN partidos p ON hr.id_partido = p.id_partido
        WHERE p.estado IN ('finalizado', 'confirmado')
        LIMIT 10
    """))
    
    for row in result:
        print(f"   Usuario {row[0]}, Partido {row[1]}: {row[2]} → {row[3]} (delta: {row[4]}, estado: {row[5]})")

finally:
    session.close()
