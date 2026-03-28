import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def buscar_cassiel():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("BÚSQUEDA: Cassiel Lucero y Desconocidos en Torneo 45")
    print("=" * 80)
    
    # Buscar Cassiel
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.nombre) LIKE '%cassiel%'
    """)
    cassiels = cur.fetchall()
    
    print(f"\n📋 Usuarios con 'Cassiel': {len(cassiels)}")
    for c in cassiels:
        print(f"   ID {c['id_usuario']}: {c['nombre']} {c['apellido']}")
        
        # Buscar parejas
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
        """, (c['id_usuario'], c['id_usuario']))
        
        parejas = cur.fetchall()
        
        if parejas:
            print(f"   Parejas:")
            for p in parejas:
                print(f"     Pareja {p['id']} - {p['zona']} - {p['categoria']}: {p['jugador1']} / {p['jugador2']}")
    
    # Buscar Desconocidos
    print("\n" + "=" * 80)
    print("DESCONOCIDOS")
    print("=" * 80)
    
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.nombre) = 'desconocido'
        ORDER BY u.id_usuario
    """)
    desconocidos = cur.fetchall()
    
    print(f"\n📋 Usuarios 'Desconocido': {len(desconocidos)}")
    for d in desconocidos:
        print(f"   ID {d['id_usuario']}: {d['nombre']} {d['apellido']}")
        
        # Buscar parejas
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
        """, (d['id_usuario'], d['id_usuario']))
        
        parejas = cur.fetchall()
        
        if parejas:
            print(f"   Parejas:")
            for p in parejas:
                print(f"     Pareja {p['id']} - {p['zona']} - {p['categoria']}: {p['jugador1']} / {p['jugador2']}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    buscar_cassiel()
