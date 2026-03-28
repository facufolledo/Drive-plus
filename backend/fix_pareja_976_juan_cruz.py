import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def fix_pareja_976():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("FIX: Pareja 976 - Juan Folledo → Juan Cruz")
    print("=" * 80)
    
    # Verificar pareja 976
    cur.execute("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id = 976
    """)
    pareja = cur.fetchone()
    
    if not pareja:
        print("❌ No se encontró pareja 976")
        cur.close()
        conn.close()
        return
    
    print(f"\n📋 Pareja 976 actual:")
    print(f"   Jugador 1 (ID {pareja['jugador1_id']}): {pareja['jugador1']}")
    print(f"   Jugador 2 (ID {pareja['jugador2_id']}): {pareja['jugador2']}")
    
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
    
    # Reemplazar jugador2 por Juan Cruz
    cur.execute("""
        UPDATE torneos_parejas
        SET jugador2_id = %s
        WHERE id = 976
    """, (juan_cruz_id,))
    
    print(f"✅ Pareja 976: jugador2 actualizado a Juan Cruz (ID {juan_cruz_id})")
    
    conn.commit()
    
    # Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL")
    print("=" * 80)
    
    cur.execute("""
        SELECT tp.id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id = 976
    """)
    pareja_final = cur.fetchone()
    
    if pareja_final:
        print(f"\n✅ Pareja 976:")
        print(f"   {pareja_final['jugador1']} / {pareja_final['jugador2']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CORRECCIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    fix_pareja_976()
