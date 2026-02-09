import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ No se encontró DATABASE_URL en .env")
    exit(1)

# Crear engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("🔍 Verificando datos de ranking en la base de datos")
print("=" * 70)

try:
    # Consultar usuarios con sus estadísticas
    query = text("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            u.rating,
            u.partidos_jugados,
            u.sexo,
            p.nombre,
            p.apellido,
            (
                SELECT COUNT(*)
                FROM historial_rating hr
                JOIN partidos pa ON hr.id_partido = pa.id_partido
                WHERE hr.id_usuario = u.id_usuario
                AND pa.estado IN ('finalizado', 'confirmado')
                AND hr.delta > 0
            ) as partidos_ganados,
            (
                SELECT SUM(hr2.delta)
                FROM historial_rating hr2
                JOIN partidos pa2 ON hr2.id_partido = pa2.id_partido
                WHERE hr2.id_usuario = u.id_usuario
                AND pa2.estado IN ('finalizado', 'confirmado')
            ) as suma_deltas
        FROM usuarios u
        LEFT JOIN perfil_usuario p ON u.id_usuario = p.id_usuario
        ORDER BY u.rating DESC
        LIMIT 10
    """)
    
    result = session.execute(query)
    usuarios = result.fetchall()
    
    if not usuarios:
        print("⚠️  No se encontraron usuarios en la base de datos")
    else:
        print(f"✅ Se encontraron {len(usuarios)} usuarios\n")
        
        for i, u in enumerate(usuarios, 1):
            print(f"{i}. Usuario ID: {u.id_usuario}")
            print(f"   Nombre: {u.nombre} {u.apellido}")
            print(f"   Username: @{u.nombre_usuario}")
            print(f"   Rating: {u.rating}")
            print(f"   Sexo: {u.sexo}")
            print(f"   Partidos jugados: {u.partidos_jugados}")
            print(f"   Partidos ganados: {u.partidos_ganados}")
            print(f"   Suma deltas: {u.suma_deltas}")
            
            # Calcular tendencia
            suma_deltas = u.suma_deltas or 0
            if suma_deltas > 10:
                tendencia = "up ↑"
            elif suma_deltas < -10:
                tendencia = "down ↓"
            elif suma_deltas != 0:
                tendencia = "stable →"
            else:
                tendencia = "neutral --"
            
            print(f"   Tendencia: {tendencia}")
            print()
        
        # Verificar si hay partidos confirmados
        query_partidos = text("""
            SELECT COUNT(*) as total
            FROM partidos
            WHERE estado IN ('finalizado', 'confirmado')
        """)
        result_partidos = session.execute(query_partidos)
        total_partidos = result_partidos.fetchone()[0]
        
        print(f"\n📊 Total de partidos finalizados/confirmados: {total_partidos}")
        
        # Verificar historial_rating
        query_historial = text("""
            SELECT COUNT(*) as total
            FROM historial_rating
        """)
        result_historial = session.execute(query_historial)
        total_historial = result_historial.fetchone()[0]
        
        print(f"📊 Total de registros en historial_rating: {total_historial}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
