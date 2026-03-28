import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def fix_pareja_993_y_alan():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("FIX: Pareja 993 y Alan Corona")
    print("=" * 80)
    
    # 1. Verificar pareja 993 actual
    print("\n1️⃣ Verificando pareja 993...")
    cur.execute("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id = 993
    """)
    pareja = cur.fetchone()
    
    if pareja:
        print(f"   📋 Pareja 993 actual:")
        print(f"      Jugador 1 (ID {pareja['jugador1_id']}): {pareja['jugador1']}")
        print(f"      Jugador 2 (ID {pareja['jugador2_id']}): {pareja['jugador2']}")
        
        # Buscar Facundo Jain (ID 1006)
        facundo_id = 1006
        
        cur.execute("""
            SELECT u.id_usuario, p.nombre, p.apellido
            FROM usuarios u
            JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.id_usuario = %s
        """, (facundo_id,))
        facundo = cur.fetchone()
        
        if facundo:
            print(f"\n   ✅ Facundo Jain encontrado: ID {facundo['id_usuario']} - {facundo['nombre']} {facundo['apellido']}")
            
            # Actualizar jugador1 de la pareja 993 a Facundo Jain
            cur.execute("""
                UPDATE torneos_parejas
                SET jugador1_id = %s
                WHERE id = 993
            """, (facundo['id_usuario'],))
            print(f"   ✅ Pareja 993: jugador1 actualizado a Facundo Jain (ID {facundo['id_usuario']})")
        else:
            print("   ⚠️  No se encontró Facundo Jain")
    
    # 2. Corregir perfil de Alan Corona (ID 890)
    print("\n2️⃣ Corrigiendo perfil de Alan Corona (ID 890)...")
    
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.id_usuario = 890
    """)
    alan = cur.fetchone()
    
    if alan:
        if not alan['nombre']:
            # Crear perfil
            cur.execute("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                VALUES (890, 'Alan', 'Corona')
            """)
            print(f"   ✅ Perfil creado: Alan Corona")
        else:
            print(f"   📋 Usuario 890 actual: {alan['nombre']} {alan['apellido']}")
            
            if 'jugador' in str(alan['nombre']).lower() or not alan['nombre']:
                # Actualizar perfil
                cur.execute("""
                    UPDATE perfil_usuarios
                    SET nombre = 'Alan', apellido = 'Corona'
                    WHERE id_usuario = 890
                """)
                print(f"   ✅ Perfil actualizado: Alan Corona")
            else:
                print(f"   ℹ️  El perfil ya tiene nombre correcto")
    else:
        print("   ⚠️  No se encontró usuario con ID 890")
    
    conn.commit()
    
    # Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL")
    print("=" * 80)
    
    # Verificar pareja 993
    cur.execute("""
        SELECT tp.id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id = 993
    """)
    p993 = cur.fetchone()
    
    if p993:
        print(f"\n✅ Pareja 993: {p993['jugador1']} / {p993['jugador2']}")
    
    # Verificar usuario 890
    cur.execute("""
        SELECT p.nombre || ' ' || p.apellido as nombre_completo
        FROM perfil_usuarios p
        WHERE p.id_usuario = 890
    """)
    alan_final = cur.fetchone()
    
    if alan_final:
        print(f"✅ Usuario 890: {alan_final['nombre_completo']}")
    
    # Verificar partido 1021
    cur.execute("""
        SELECT p.id,
               pu1.nombre || ' ' || pu1.apellido as j1_p1,
               pu2.nombre || ' ' || pu2.apellido as j2_p1,
               pu3.nombre || ' ' || pu3.apellido as j1_p2,
               pu4.nombre || ' ' || pu4.apellido as j2_p2
        FROM torneo_partidos p
        LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        LEFT JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        LEFT JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        LEFT JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id = 1021
    """)
    p1021 = cur.fetchone()
    
    if p1021:
        print(f"\n✅ Partido 1021:")
        print(f"   {p1021['j1_p1']} / {p1021['j2_p1']}")
        print(f"   vs")
        print(f"   {p1021['j1_p2']} / {p1021['j2_p2']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CORRECCIONES COMPLETADAS")
    print("=" * 80)

if __name__ == "__main__":
    fix_pareja_993_y_alan()
