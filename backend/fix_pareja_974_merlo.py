import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def fix_pareja_merlo():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("FIX: Pareja 974 - Emiliano Merlo duplicado")
    print("=" * 80)
    
    # Verificar pareja 974
    cur.execute("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2,
               tc.nombre as categoria
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
        WHERE tp.id = 974
    """)
    pareja = cur.fetchone()
    
    if not pareja:
        print("❌ No se encontró pareja 974")
        cur.close()
        conn.close()
        return
    
    print(f"\n📋 Pareja 974 actual - {pareja['categoria']}:")
    print(f"   Jugador 1 (ID {pareja['jugador1_id']}): {pareja['jugador1']}")
    print(f"   Jugador 2 (ID {pareja['jugador2_id']}): {pareja['jugador2']}")
    
    # Verificar si Leo Merlo ya existe
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.nombre) = 'leo' AND LOWER(p.apellido) = 'merlo'
    """)
    leo = cur.fetchone()
    
    if leo:
        leo_id = leo['id_usuario']
        print(f"\n✅ Leo Merlo ya existe: ID {leo_id}")
    else:
        # Crear usuario Leo Merlo
        cur.execute("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, partidos_jugados)
            VALUES ('leo.merlo.t45', 'leo.merlo.t45@temp.com', 'temp_hash', 1200, 0)
            RETURNING id_usuario
        """)
        leo_id = cur.fetchone()['id_usuario']
        
        cur.execute("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
            VALUES (%s, 'Leo', 'Merlo')
        """, (leo_id,))
        
        print(f"\n✅ Usuario Leo Merlo creado: ID {leo_id}")
    
    # Reemplazar jugador2 por Leo Merlo
    cur.execute("""
        UPDATE torneos_parejas
        SET jugador2_id = %s
        WHERE id = 974
    """, (leo_id,))
    
    print(f"✅ Pareja 974: jugador2 actualizado a Leo Merlo (ID {leo_id})")
    
    conn.commit()
    
    # Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL")
    print("=" * 80)
    
    cur.execute("""
        SELECT tp.id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2,
               tc.nombre as categoria
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
        WHERE tp.id = 974
    """)
    pareja_final = cur.fetchone()
    
    if pareja_final:
        print(f"\n✅ Pareja 974 - {pareja_final['categoria']}:")
        print(f"   {pareja_final['jugador1']} / {pareja_final['jugador2']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CORRECCIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    fix_pareja_merlo()
