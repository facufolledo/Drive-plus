"""
Script para actualizar el campo partidos_jugados de todos los usuarios
basándose en los registros de historial_rating
"""
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

print("🔄 Actualizando campo partidos_jugados de todos los usuarios")
print("=" * 70)

try:
    # 1. Verificar estado actual
    query_antes = text("""
        SELECT COUNT(*) as total
        FROM usuarios
        WHERE partidos_jugados > 0
    """)
    result_antes = session.execute(query_antes)
    total_antes = result_antes.fetchone()[0]
    
    print(f"\n📊 Estado ANTES:")
    print(f"   Usuarios con partidos_jugados > 0: {total_antes}")
    
    # 2. Actualizar partidos_jugados desde historial_rating
    query_update = text("""
        UPDATE usuarios u
        SET partidos_jugados = (
            SELECT COUNT(DISTINCT hr.id_partido)
            FROM historial_rating hr
            JOIN partidos p ON hr.id_partido = p.id_partido
            WHERE hr.id_usuario = u.id_usuario
            AND p.estado IN ('finalizado', 'confirmado')
        )
        WHERE EXISTS (
            SELECT 1
            FROM historial_rating hr
            WHERE hr.id_usuario = u.id_usuario
        )
    """)
    
    result = session.execute(query_update)
    session.commit()
    
    print(f"\n✅ Actualización completada")
    print(f"   Filas afectadas: {result.rowcount}")
    
    # 3. Verificar estado después
    query_despues = text("""
        SELECT COUNT(*) as total
        FROM usuarios
        WHERE partidos_jugados > 0
    """)
    result_despues = session.execute(query_despues)
    total_despues = result_despues.fetchone()[0]
    
    print(f"\n📊 Estado DESPUÉS:")
    print(f"   Usuarios con partidos_jugados > 0: {total_despues}")
    
    # 4. Mostrar algunos ejemplos
    query_ejemplos = text("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            u.partidos_jugados,
            (
                SELECT COUNT(*)
                FROM historial_rating hr
                JOIN partidos p ON hr.id_partido = p.id_partido
                WHERE hr.id_usuario = u.id_usuario
                AND p.estado IN ('finalizado', 'confirmado')
                AND hr.delta > 0
            ) as partidos_ganados
        FROM usuarios u
        WHERE u.partidos_jugados > 0
        ORDER BY u.partidos_jugados DESC
        LIMIT 10
    """)
    result_ejemplos = session.execute(query_ejemplos)
    ejemplos = result_ejemplos.fetchall()
    
    if ejemplos:
        print(f"\n📊 Top 10 usuarios con más partidos:")
        for u in ejemplos:
            porcentaje = 0
            if u.partidos_jugados > 0:
                porcentaje = round((u.partidos_ganados / u.partidos_jugados) * 100)
            print(f"   - {u.nombre_usuario} (ID:{u.id_usuario}): {u.partidos_jugados} partidos, {u.partidos_ganados} ganados ({porcentaje}%)")
    
    print(f"\n✅ Script completado exitosamente")
    print(f"\n⚠️  IMPORTANTE: Ahora debes hacer commit y push del fix en ranking_controller.py")
    print(f"   para que el endpoint /ranking/ use estos valores actualizados")

except Exception as e:
    session.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
