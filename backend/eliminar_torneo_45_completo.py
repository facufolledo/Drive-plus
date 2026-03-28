import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def eliminar_torneo_45():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("ELIMINAR TORNEO 45 Y USUARIOS TEMPORALES")
    print("=" * 80)
    
    # 1. Identificar usuarios temporales del Torneo 45 que NO tienen partidos en otros torneos
    print("\n1️⃣ Identificando usuarios temporales del Torneo 45...")
    
    cur.execute("""
        SELECT DISTINCT u.id_usuario, u.email, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.id_usuario IN (
            SELECT DISTINCT jugador1_id FROM torneos_parejas WHERE torneo_id = 45
            UNION
            SELECT DISTINCT jugador2_id FROM torneos_parejas WHERE torneo_id = 45
        )
        AND (
            u.email LIKE '%@temp.com' 
            OR u.email LIKE '%@driveplus.temp'
            OR u.email LIKE '%.t45@%'
        )
        ORDER BY u.id_usuario
    """)
    
    usuarios_temp_t45 = cur.fetchall()
    
    print(f"\n📋 Usuarios temporales en Torneo 45: {len(usuarios_temp_t45)}")
    
    usuarios_a_eliminar = []
    usuarios_a_mantener = []
    
    for u in usuarios_temp_t45:
        # Verificar si tiene parejas en otros torneos
        cur.execute("""
            SELECT COUNT(*) as count
            FROM torneos_parejas
            WHERE (jugador1_id = %s OR jugador2_id = %s)
            AND torneo_id != 45
        """, (u['id_usuario'], u['id_usuario']))
        
        count = cur.fetchone()['count']
        
        if count > 0:
            usuarios_a_mantener.append(u)
            print(f"   🔒 MANTENER ID {u['id_usuario']}: {u['nombre']} {u['apellido']} ({count} parejas en otros torneos)")
        else:
            usuarios_a_eliminar.append(u)
            print(f"   🗑️  ELIMINAR ID {u['id_usuario']}: {u['nombre']} {u['apellido']}")
    
    # 2. Eliminar partidos de la tabla 'partidos' (antigua) que referencian parejas del torneo 45
    print(f"\n2️⃣ Eliminando partidos de tabla 'partidos' que referencian parejas del Torneo 45...")
    
    cur.execute("""
        DELETE FROM partidos 
        WHERE pareja1_id IN (SELECT id FROM torneos_parejas WHERE torneo_id = 45)
           OR pareja2_id IN (SELECT id FROM torneos_parejas WHERE torneo_id = 45)
    """)
    
    partidos_eliminados = cur.rowcount
    print(f"   ✅ {partidos_eliminados} partidos eliminados de tabla 'partidos'")
    
    # 3. Eliminar el Torneo 45 (esto eliminará en cascada: parejas, zonas, categorías, etc.)
    print(f"\n3️⃣ Eliminando Torneo 45...")
    
    cur.execute("""
        DELETE FROM torneos WHERE id = 45
    """)
    
    print(f"   ✅ Torneo 45 eliminado (con todas sus parejas, zonas, categorías, etc.)")
    
    # 4. Eliminar usuarios temporales que no tienen otras parejas
    print(f"\n4️⃣ Eliminando usuarios temporales sin otras parejas...")
    
    for u in usuarios_a_eliminar:
        # Eliminar perfil primero
        cur.execute("""
            DELETE FROM perfil_usuarios WHERE id_usuario = %s
        """, (u['id_usuario'],))
        
        # Eliminar usuario
        cur.execute("""
            DELETE FROM usuarios WHERE id_usuario = %s
        """, (u['id_usuario'],))
        
        print(f"   ✅ Eliminado ID {u['id_usuario']}: {u['nombre']} {u['apellido']}")
    
    conn.commit()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    
    print(f"\n✅ Torneo 45: ELIMINADO")
    print(f"✅ Usuarios temporales eliminados: {len(usuarios_a_eliminar)}")
    print(f"🔒 Usuarios temporales mantenidos (tienen partidos en otros torneos): {len(usuarios_a_mantener)}")
    
    if usuarios_a_mantener:
        print(f"\n📋 Usuarios mantenidos:")
        for u in usuarios_a_mantener:
            print(f"   ID {u['id_usuario']}: {u['nombre']} {u['apellido']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ LIMPIEZA COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    eliminar_torneo_45()
