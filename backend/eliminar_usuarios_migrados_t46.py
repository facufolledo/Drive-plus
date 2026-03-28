import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("ELIMINAR USUARIOS MIGRADOS")
print("=" * 80)

usuarios_a_eliminar = [175, 1102, 1154]

for user_id in usuarios_a_eliminar:
    print(f"\n{'=' * 80}")
    print(f"ELIMINAR USUARIO {user_id}")
    print("=" * 80)
    
    # Ver datos del usuario
    cur.execute("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            u.email,
            pu.nombre,
            pu.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
        WHERE u.id_usuario = %s
    """, (user_id,))
    
    usuario = cur.fetchone()
    
    if usuario:
        print(f"\nUsuario: {usuario['nombre']} {usuario['apellido']}")
        print(f"  Email: {usuario['email']}")
        
        # Verificar que no tenga referencias
        cur.execute("""
            SELECT COUNT(*) as total FROM torneos_parejas 
            WHERE (jugador1_id = %s OR jugador2_id = %s)
            AND torneo_id = 46
        """, (user_id, user_id))
        
        parejas = cur.fetchone()['total']
        
        if parejas > 0:
            print(f"\n⚠️  ERROR: Usuario {user_id} todavía tiene {parejas} parejas en T46")
            print(f"   NO SE PUEDE ELIMINAR")
            continue
        
        # Eliminar perfil_usuarios
        cur.execute("""
            DELETE FROM perfil_usuarios WHERE id_usuario = %s
            RETURNING id_usuario
        """, (user_id,))
        
        perfil_deleted = cur.fetchone()
        if perfil_deleted:
            print(f"  ✅ Perfil eliminado")
        
        # Eliminar usuarios
        cur.execute("""
            DELETE FROM usuarios WHERE id_usuario = %s
            RETURNING id_usuario
        """, (user_id,))
        
        usuario_deleted = cur.fetchone()
        if usuario_deleted:
            print(f"  ✅ Usuario eliminado")
    else:
        print(f"\n⚠️  Usuario {user_id} no encontrado")

conn.commit()

print("\n" + "=" * 80)
print("✅ USUARIOS ELIMINADOS")
print("=" * 80)

cur.close()
conn.close()
