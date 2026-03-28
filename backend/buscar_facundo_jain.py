import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def buscar_facundo():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("BÚSQUEDA: Facundo Jain")
    print("=" * 80)
    
    # Buscar por nombre Facundo
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.nombre) LIKE '%facundo%' OR LOWER(p.apellido) LIKE '%facundo%'
        ORDER BY u.id_usuario
    """)
    facundos = cur.fetchall()
    
    print(f"\n📋 Usuarios con 'Facundo': {len(facundos)}")
    for f in facundos:
        print(f"   ID {f['id_usuario']}: {f['nombre']} {f['apellido']} - {f['email']}")
    
    # Buscar por apellido Jain
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.apellido) LIKE '%jain%' OR LOWER(p.nombre) LIKE '%jain%'
        ORDER BY u.id_usuario
    """)
    jains = cur.fetchall()
    
    print(f"\n📋 Usuarios con 'Jain': {len(jains)}")
    for j in jains:
        print(f"   ID {j['id_usuario']}: {j['nombre']} {j['apellido']} - {j['email']}")
    
    # Buscar usuario 890 (Alan Corona)
    print("\n" + "=" * 80)
    print("USUARIO 890")
    print("=" * 80)
    
    cur.execute("""
        SELECT u.id_usuario, u.nombre_usuario, p.nombre, p.apellido, u.email
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.id_usuario = 890
    """)
    user890 = cur.fetchone()
    
    if user890:
        print(f"\nID: {user890['id_usuario']}")
        print(f"Username: {user890['nombre_usuario']}")
        print(f"Nombre: {user890['nombre']}")
        print(f"Apellido: {user890['apellido']}")
        print(f"Email: {user890['email']}")
        
        # Ver si tiene perfil
        if not user890['nombre']:
            print("\n⚠️  Este usuario NO tiene perfil en perfil_usuarios")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    buscar_facundo()
