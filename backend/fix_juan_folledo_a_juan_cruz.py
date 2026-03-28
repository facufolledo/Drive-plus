import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def fix_juan_folledo():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("FIX: Juan Folledo → Juan Cruz")
    print("=" * 80)
    
    # Buscar usuario Juan Folledo
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.apellido) LIKE '%folledo%'
    """)
    folledo = cur.fetchone()
    
    if not folledo:
        print("❌ No se encontró usuario con apellido Folledo")
        cur.close()
        conn.close()
        return
    
    folledo_id = folledo['id_usuario']
    print(f"\n📋 Usuario encontrado:")
    print(f"   ID: {folledo_id}")
    print(f"   Nombre: {folledo['nombre']} {folledo['apellido']}")
    print(f"   Email: {folledo['email']}")
    
    # Buscar parejas de Juan Folledo en Torneo 45
    cur.execute("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2,
               tc.nombre as categoria,
               tz.nombre as zona
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
        LEFT JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
        LEFT JOIN torneo_zonas tz ON tzp.zona_id = tz.id
        WHERE tp.torneo_id = 45
        AND (tp.jugador1_id = %s OR tp.jugador2_id = %s)
    """, (folledo_id, folledo_id))
    
    parejas = cur.fetchall()
    
    if not parejas:
        print(f"\n❌ No se encontraron parejas de Juan Folledo en Torneo 45")
        cur.close()
        conn.close()
        return
    
    print(f"\n📋 Parejas de Juan Folledo en Torneo 45:")
    for p in parejas:
        print(f"   Pareja {p['id']} - {p['zona']} - {p['categoria']}")
        print(f"   {p['jugador1']} / {p['jugador2']}")
    
    # Verificar si Juan Cruz ya existe
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.nombre) = 'juan' AND LOWER(p.apellido) = 'cruz'
    """)
    juan_cruz = cur.fetchone()
    
    if juan_cruz:
        juan_cruz_id = juan_cruz['id_usuario']
        print(f"\n✅ Juan Cruz ya existe: ID {juan_cruz_id}")
    else:
        # Crear usuario Juan Cruz
        cur.execute("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, partidos_jugados)
            VALUES ('juan.cruz.t45', 'juan.cruz.t45@temp.com', 'temp_hash', 1200, 0)
            RETURNING id_usuario
        """)
        juan_cruz_id = cur.fetchone()['id_usuario']
        
        cur.execute("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
            VALUES (%s, 'Juan', 'Cruz')
        """, (juan_cruz_id,))
        
        print(f"\n✅ Usuario Juan Cruz creado: ID {juan_cruz_id}")
    
    # Reemplazar Juan Folledo por Juan Cruz en todas las parejas
    for p in parejas:
        if p['jugador1_id'] == folledo_id:
            cur.execute("""
                UPDATE torneos_parejas
                SET jugador1_id = %s
                WHERE id = %s
            """, (juan_cruz_id, p['id']))
            print(f"\n✅ Pareja {p['id']}: jugador1 actualizado (Folledo → Cruz)")
        elif p['jugador2_id'] == folledo_id:
            cur.execute("""
                UPDATE torneos_parejas
                SET jugador2_id = %s
                WHERE id = %s
            """, (juan_cruz_id, p['id']))
            print(f"✅ Pareja {p['id']}: jugador2 actualizado (Folledo → Cruz)")
    
    conn.commit()
    
    # Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL")
    print("=" * 80)
    
    cur.execute("""
        SELECT tp.id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2,
               tc.nombre as categoria,
               tz.nombre as zona
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
        LEFT JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
        LEFT JOIN torneo_zonas tz ON tzp.zona_id = tz.id
        WHERE tp.torneo_id = 45
        AND (tp.jugador1_id = %s OR tp.jugador2_id = %s)
    """, (juan_cruz_id, juan_cruz_id))
    
    parejas_final = cur.fetchall()
    
    if parejas_final:
        print(f"\n✅ Parejas de Juan Cruz:")
        for p in parejas_final:
            print(f"   Pareja {p['id']} - {p['zona']} - {p['categoria']}")
            print(f"   {p['jugador1']} / {p['jugador2']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CORRECCIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    fix_juan_folledo()
