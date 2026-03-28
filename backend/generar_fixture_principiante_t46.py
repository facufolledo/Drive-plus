import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Configurar el path correctamente
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, backend_dir)
sys.path.insert(0, src_dir)

# Ahora importar
from src.services.torneo_fixture_global_service import TorneoFixtureGlobalService
from src.database import get_db

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("GENERAR FIXTURE PRINCIPIANTE - TORNEO 46")
print("=" * 80)

try:
    # 1. Eliminar partidos existentes de Principiante
    print("\n🗑️  Eliminando partidos existentes de Principiante...")
    
    cur.execute("""
        DELETE FROM partidos
        WHERE id_torneo = 46
        AND categoria_id = (SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = 'Principiante')
    """)
    
    partidos_eliminados = cur.rowcount
    print(f"   ✅ {partidos_eliminados} partidos eliminados")
    
    conn.commit()
    
    # 2. Obtener información del torneo
    cur.execute("""
        SELECT 
            t.id,
            t.nombre,
            t.fecha_inicio,
            t.fecha_fin
        FROM torneos t
        WHERE t.id = 46
    """)
    
    torneo = cur.fetchone()
    
    if not torneo:
        print("❌ Torneo 46 no encontrado")
        cur.close()
        conn.close()
        exit(1)
    
    print(f"\n📋 TORNEO: {torneo['nombre']}")
    print(f"   Fecha inicio: {torneo['fecha_inicio']}")
    print(f"   Fecha fin: {torneo['fecha_fin']}")
    
    # 3. Obtener categoría Principiante
    cur.execute("""
        SELECT id, nombre
        FROM torneo_categorias
        WHERE torneo_id = 46 AND nombre = 'Principiante'
    """)
    
    categoria = cur.fetchone()
    categoria_id = categoria['id']
    
    print(f"\n✅ Categoría: {categoria['nombre']} (ID: {categoria_id})")
    
    # 4. Verificar zonas
    cur.execute("""
        SELECT id, nombre
        FROM torneo_zonas
        WHERE torneo_id = 46
        AND categoria_id = %s
        ORDER BY numero_orden
    """, (categoria_id,))
    
    zonas = cur.fetchall()
    print(f"\n📊 ZONAS ({len(zonas)}):")
    for z in zonas:
        print(f"   - {z['nombre']} (ID: {z['id']})")
    
    # 5. Verificar parejas por zona
    print(f"\n📋 PAREJAS POR ZONA:")
    
    zonas_parejas = {
        400: [1048, 1042, 1041],  # Zona A
        401: [1043, 1044, 1045],  # Zona B
        402: [1046, 1047, 1049],  # Zona C
        403: [1050, 1051, 1052]   # Zona D
    }
    
    for zona_id, parejas_ids in zonas_parejas.items():
        cur.execute("SELECT nombre FROM torneo_zonas WHERE id = %s", (zona_id,))
        zona_nombre = cur.fetchone()['nombre']
        
        print(f"\n   {zona_nombre}:")
        for pareja_id in parejas_ids:
            cur.execute("""
                SELECT 
                    pu1.nombre || ' ' || pu1.apellido as j1,
                    pu2.nombre || ' ' || pu2.apellido as j2
                FROM torneos_parejas tp
                JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
                JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
                WHERE tp.id = %s
            """, (pareja_id,))
            pareja = cur.fetchone()
            print(f"     - Pareja {pareja_id}: {pareja['j1']} / {pareja['j2']}")
    
    cur.close()
    conn.close()
    
    # 6. Usar el servicio de generación de fixture
    print(f"\n" + "=" * 80)
    print("GENERANDO FIXTURE CON EL SERVICIO")
    print("=" * 80)
    
    # Crear una sesión de base de datos
    db = next(get_db())
    
    try:
        # Instanciar el servicio
        fixture_service = TorneoFixtureGlobalService(db)
        
        # Generar fixture para el torneo 46
        resultado = fixture_service.generar_fixture_global(
            torneo_id=46,
            usuario_id=1  # ID del admin/organizador
        )
        
        print(f"\n✅ FIXTURE GENERADO EXITOSAMENTE")
        print(f"\n📊 RESULTADO:")
        print(f"   Mensaje: {resultado.get('message', 'N/A')}")
        
        if 'partidos_creados' in resultado:
            print(f"   Partidos creados: {resultado['partidos_creados']}")
        
        if 'partidos_programados' in resultado:
            print(f"   Partidos programados: {resultado['partidos_programados']}")
        
        if 'categorias_procesadas' in resultado:
            print(f"   Categorías procesadas: {', '.join(resultado['categorias_procesadas'])}")
        
        # Verificar partidos creados
        conn2 = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
        cur2 = conn2.cursor(cursor_factory=RealDictCursor)
        
        cur2.execute("""
            SELECT COUNT(*) as total
            FROM partidos
            WHERE id_torneo = 46
            AND categoria_id = %s
        """, (categoria_id,))
        
        total_partidos = cur2.fetchone()['total']
        
        cur2.execute("""
            SELECT COUNT(*) as con_horario
            FROM partidos
            WHERE id_torneo = 46
            AND categoria_id = %s
            AND fecha_hora IS NOT NULL
        """, (categoria_id,))
        
        con_horario = cur2.fetchone()['con_horario']
        
        print(f"\n📈 VERIFICACIÓN:")
        print(f"   Total partidos: {total_partidos}")
        print(f"   Con horario: {con_horario}")
        print(f"   Sin horario: {total_partidos - con_horario}")
        
        cur2.close()
        conn2.close()
        
    finally:
        db.close()
    
    print(f"\n" + "=" * 80)
    print("✅ PROCESO COMPLETADO")
    print("=" * 80)

except Exception as e:
    if 'conn' in locals():
        conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
