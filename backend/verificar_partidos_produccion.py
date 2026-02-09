import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno de PRODUCCIÓN
load_dotenv('.env.production')

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ No se encontró DATABASE_URL en .env.production")
    exit(1)

# Crear engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("🔍 Verificando partidos en PRODUCCIÓN")
print("=" * 70)

try:
    # 1. Contar partidos por estado
    query_estados = text("""
        SELECT estado, COUNT(*) as total
        FROM partidos
        GROUP BY estado
        ORDER BY total DESC
    """)
    
    result = session.execute(query_estados)
    estados = result.fetchall()
    
    print("\n📊 Partidos por estado:")
    for estado in estados:
        print(f"   - {estado.estado}: {estado.total}")
    
    # 2. Contar registros en historial_rating
    query_historial = text("""
        SELECT COUNT(*) as total
        FROM historial_rating
    """)
    result_historial = session.execute(query_historial)
    total_historial = result_historial.fetchone()[0]
    
    print(f"\n📊 Total de registros en historial_rating: {total_historial}")
    
    # 3. Verificar usuarios con partidos_jugados > 0
    query_usuarios = text("""
        SELECT COUNT(*) as total
        FROM usuarios
        WHERE partidos_jugados > 0
    """)
    result_usuarios = session.execute(query_usuarios)
    total_usuarios_con_partidos = result_usuarios.fetchone()[0]
    
    print(f"📊 Usuarios con partidos_jugados > 0: {total_usuarios_con_partidos}")
    
    # 4. Ver algunos usuarios con más partidos
    query_top = text("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            u.rating,
            u.partidos_jugados,
            (
                SELECT COUNT(*)
                FROM historial_rating hr
                JOIN partidos p ON hr.id_partido = p.id_partido
                WHERE hr.id_usuario = u.id_usuario
                AND p.estado IN ('finalizado', 'confirmado')
                AND hr.delta > 0
            ) as partidos_ganados_calculados
        FROM usuarios u
        WHERE u.partidos_jugados > 0
        ORDER BY u.partidos_jugados DESC
        LIMIT 5
    """)
    result_top = session.execute(query_top)
    top_usuarios = result_top.fetchall()
    
    if top_usuarios:
        print(f"\n📊 Top 5 usuarios con más partidos:")
        for u in top_usuarios:
            print(f"   - {u.nombre_usuario} (ID:{u.id_usuario}): {u.partidos_jugados} partidos, {u.partidos_ganados_calculados} ganados")
    else:
        print(f"\n⚠️  No hay usuarios con partidos_jugados > 0")
    
    # 5. Verificar si hay partidos confirmados
    query_confirmados = text("""
        SELECT COUNT(*) as total
        FROM partidos
        WHERE estado IN ('finalizado', 'confirmado')
    """)
    result_confirmados = session.execute(query_confirmados)
    total_confirmados = result_confirmados.fetchone()[0]
    
    print(f"\n📊 Partidos finalizados/confirmados: {total_confirmados}")
    
    if total_confirmados == 0:
        print(f"\n⚠️  PROBLEMA: No hay partidos confirmados en la base de datos")
        print(f"   Por eso todos los usuarios tienen 0 partidos ganados")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
