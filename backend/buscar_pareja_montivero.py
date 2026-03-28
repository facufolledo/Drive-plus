import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def buscar_montivero():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("BÚSQUEDA: Pareja con Montivero")
    print("=" * 80)
    
    # Buscar usuario Montivero
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.apellido) LIKE '%montivero%' OR LOWER(p.nombre) LIKE '%montivero%'
    """)
    montiveros = cur.fetchall()
    
    print(f"\n📋 Usuarios con 'Montivero': {len(montiveros)}")
    for m in montiveros:
        print(f"   ID {m['id_usuario']}: {m['nombre']} {m['apellido']} - {m['email']}")
    
    if not montiveros:
        print("\n❌ No se encontraron usuarios con Montivero")
        cur.close()
        conn.close()
        return
    
    # Buscar parejas de Montivero en Torneo 45
    for m in montiveros:
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
        """, (m['id_usuario'], m['id_usuario']))
        
        parejas = cur.fetchall()
        
        if parejas:
            print(f"\n📋 Parejas de {m['nombre']} {m['apellido']} (ID {m['id_usuario']}):")
            for p in parejas:
                print(f"   Pareja {p['id']} - {p['zona']} - {p['categoria']}")
                print(f"   Jugador 1 (ID {p['jugador1_id']}): {p['jugador1']}")
                print(f"   Jugador 2 (ID {p['jugador2_id']}): {p['jugador2']}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    buscar_montivero()
