"""
Verificar si hay partidos con elo_aplicado = False
Esto indicaría que hubo errores al aplicar ELO
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno de PRODUCCIÓN
load_dotenv('.env.production')

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ No se encontró DATABASE_URL")
    exit(1)

# Crear engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("🔍 Verificando partidos con problemas de ELO")
print("=" * 70)

try:
    # 1. Contar partidos por elo_aplicado
    query_elo = text("""
        SELECT 
            elo_aplicado,
            COUNT(*) as total
        FROM partidos
        WHERE estado IN ('finalizado', 'confirmado')
        GROUP BY elo_aplicado
    """)
    
    result = session.execute(query_elo)
    estados_elo = result.fetchall()
    
    print("\n📊 Partidos confirmados por elo_aplicado:")
    for estado in estados_elo:
        elo_status = "✅ TRUE" if estado.elo_aplicado else "❌ FALSE" if estado.elo_aplicado == False else "⚠️  NULL"
        print(f"   {elo_status}: {estado.total} partidos")
    
    # 2. Ver partidos con elo_aplicado = False
    query_false = text("""
        SELECT 
            id_partido,
            id_torneo,
            pareja1_id,
            pareja2_id,
            estado,
            elo_aplicado,
            fecha_hora
        FROM partidos
        WHERE estado IN ('finalizado', 'confirmado')
        AND (elo_aplicado = FALSE OR elo_aplicado IS NULL)
        ORDER BY fecha_hora DESC
        LIMIT 10
    """)
    
    result_false = session.execute(query_false)
    partidos_false = result_false.fetchall()
    
    if partidos_false:
        print(f"\n⚠️  Partidos con ELO NO aplicado:")
        for p in partidos_false:
            print(f"   - Partido {p.id_partido} (Torneo {p.id_torneo}): {p.estado}, elo_aplicado={p.elo_aplicado}")
    else:
        print(f"\n✅ Todos los partidos tienen ELO aplicado correctamente")
    
    # 3. Verificar si hay usuarios sin partidos_jugados pero con historial
    query_usuarios = text("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            u.partidos_jugados,
            COUNT(DISTINCT hr.id_partido) as partidos_en_historial
        FROM usuarios u
        JOIN historial_rating hr ON u.id_usuario = hr.id_usuario
        JOIN partidos p ON hr.id_partido = p.id_partido
        WHERE p.estado IN ('finalizado', 'confirmado')
        GROUP BY u.id_usuario, u.nombre_usuario, u.partidos_jugados
        HAVING u.partidos_jugados != COUNT(DISTINCT hr.id_partido)
        LIMIT 10
    """)
    
    result_usuarios = session.execute(query_usuarios)
    usuarios_desincronizados = result_usuarios.fetchall()
    
    if usuarios_desincronizados:
        print(f"\n⚠️  Usuarios con partidos_jugados desincronizado:")
        for u in usuarios_desincronizados:
            print(f"   - {u.nombre_usuario} (ID:{u.id_usuario}): campo={u.partidos_jugados}, real={u.partidos_en_historial}")
    else:
        print(f"\n✅ Todos los usuarios tienen partidos_jugados sincronizado")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
