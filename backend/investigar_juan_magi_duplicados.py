import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def investigar_juan_magi():
    # Convertir URL de SQLAlchemy a psycopg2
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("INVESTIGACIÓN: Usuarios 'Juan Magi' duplicados")
    print("=" * 80)
    
    # Buscar todos los usuarios con nombres similares a "Magi"
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email, p.telefono, u.creado_en, u.rating
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.apellido) LIKE '%magi%' OR LOWER(p.nombre) LIKE '%magi%'
        ORDER BY u.creado_en
    """)
    
    usuarios = cur.fetchall()
    
    print(f"\n📋 Usuarios encontrados con 'Magi': {len(usuarios)}")
    print("-" * 80)
    
    for u in usuarios:
        print(f"\nID: {u['id_usuario']}")
        print(f"  Nombre completo: {u['nombre']} {u['apellido']}")
        print(f"  Email: {u['email']}")
        print(f"  Teléfono: {u['telefono']}")
        print(f"  Rating: {u['rating']}")
        print(f"  Creado: {u['creado_en']}")
        
        # Ver parejas de este usuario
        cur.execute("""
            SELECT tp.id, tp.torneo_id, t.nombre as torneo_nombre,
                   pu1.nombre || ' ' || pu1.apellido as jugador1,
                   pu2.nombre || ' ' || pu2.apellido as jugador2,
                   tp.estado
            FROM torneos_parejas tp
            LEFT JOIN torneos t ON tp.torneo_id = t.id
            LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tp.jugador1_id = %s OR tp.jugador2_id = %s
            ORDER BY tp.torneo_id DESC
        """, (u['id_usuario'], u['id_usuario']))
        
        parejas = cur.fetchall()
        
        if parejas:
            print(f"  🎾 Parejas ({len(parejas)}):")
            for p in parejas:
                print(f"    - Pareja ID {p['id']}: {p['jugador1']} / {p['jugador2']}")
                print(f"      Torneo: {p['torneo_nombre']} (ID {p['torneo_id']})")
                print(f"      Estado: {p['estado']}")
        else:
            print(f"  ❌ Sin parejas")
    
    print("\n" + "=" * 80)
    print("RECOMENDACIÓN:")
    print("=" * 80)
    
    # Identificar el usuario correcto (el que tiene email real)
    usuario_correcto = None
    usuarios_duplicados = []
    
    for u in usuarios:
        if u['email'] and '@' in u['email'] and not u['email'].startswith('temp_'):
            usuario_correcto = u
        elif u['email'] and u['email'].startswith('temp_'):
            usuarios_duplicados.append(u)
    
    if usuario_correcto:
        print(f"\n✅ Usuario CORRECTO identificado:")
        print(f"   ID {usuario_correcto['id_usuario']}: {usuario_correcto['nombre']} {usuario_correcto['apellido']}")
        print(f"   Email: {usuario_correcto['email']}")
        
        if usuarios_duplicados:
            print(f"\n⚠️  Usuarios DUPLICADOS a eliminar/migrar:")
            for u in usuarios_duplicados:
                print(f"   ID {u['id_usuario']}: {u['nombre']} {u['apellido']} ({u['email']})")
    else:
        print("\n⚠️  No se pudo identificar automáticamente el usuario correcto")
        print("   Revisar manualmente cuál tiene el email real")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    investigar_juan_magi()
