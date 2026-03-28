import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def verificar_eliminacion():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("VERIFICACIÓN POST-ELIMINACIÓN TORNEO 45")
    print("=" * 80)
    
    # 1. Verificar si existe el torneo 45
    print("\n1️⃣ Verificando existencia del Torneo 45...")
    cur.execute("SELECT * FROM torneos WHERE id = 45")
    torneo = cur.fetchone()
    
    if torneo:
        print(f"   ❌ ERROR: El Torneo 45 AÚN EXISTE")
        print(f"   Nombre: {torneo['nombre']}")
    else:
        print(f"   ✅ Torneo 45 eliminado correctamente")
    
    # 2. Verificar parejas del torneo 45
    print("\n2️⃣ Verificando parejas del Torneo 45...")
    cur.execute("SELECT COUNT(*) as count FROM torneos_parejas WHERE torneo_id = 45")
    parejas_count = cur.fetchone()['count']
    
    if parejas_count > 0:
        print(f"   ❌ ERROR: Aún existen {parejas_count} parejas del Torneo 45")
    else:
        print(f"   ✅ Todas las parejas eliminadas")
    
    # 3. Verificar partidos del torneo 45
    print("\n3️⃣ Verificando partidos del Torneo 45...")
    cur.execute("SELECT COUNT(*) as count FROM partidos WHERE id_torneo = 45")
    partidos_count = cur.fetchone()['count']
    
    if partidos_count > 0:
        print(f"   ❌ ERROR: Aún existen {partidos_count} partidos del Torneo 45")
    else:
        print(f"   ✅ Todos los partidos eliminados")
    
    # 4. Verificar zonas del torneo 45
    print("\n4️⃣ Verificando zonas del Torneo 45...")
    cur.execute("SELECT COUNT(*) as count FROM torneo_zonas WHERE torneo_id = 45")
    zonas_count = cur.fetchone()['count']
    
    if zonas_count > 0:
        print(f"   ❌ ERROR: Aún existen {zonas_count} zonas del Torneo 45")
    else:
        print(f"   ✅ Todas las zonas eliminadas")
    
    # 5. Verificar categorías del torneo 45
    print("\n5️⃣ Verificando categorías del Torneo 45...")
    cur.execute("SELECT COUNT(*) as count FROM torneo_categorias WHERE torneo_id = 45")
    categorias_count = cur.fetchone()['count']
    
    if categorias_count > 0:
        print(f"   ❌ ERROR: Aún existen {categorias_count} categorías del Torneo 45")
    else:
        print(f"   ✅ Todas las categorías eliminadas")
    
    # 6. Buscar usuarios temporales que quedaron huérfanos
    print("\n6️⃣ Buscando usuarios temporales huérfanos...")
    cur.execute("""
        SELECT u.id_usuario, u.email, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE (
            u.email LIKE '%@temp.com' 
            OR u.email LIKE '%@driveplus.temp'
            OR u.email LIKE '%.t45@%'
        )
        AND NOT EXISTS (
            SELECT 1 FROM torneos_parejas tp 
            WHERE tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario
        )
        ORDER BY u.id_usuario
    """)
    
    usuarios_huerfanos = cur.fetchall()
    
    if usuarios_huerfanos:
        print(f"   ⚠️  Encontrados {len(usuarios_huerfanos)} usuarios temporales sin parejas:")
        for u in usuarios_huerfanos[:10]:  # Mostrar solo los primeros 10
            print(f"      ID {u['id_usuario']}: {u['nombre']} {u['apellido']} ({u['email']})")
        if len(usuarios_huerfanos) > 10:
            print(f"      ... y {len(usuarios_huerfanos) - 10} más")
    else:
        print(f"   ✅ No hay usuarios temporales huérfanos")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("VERIFICACIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    verificar_eliminacion()
