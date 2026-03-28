import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def buscar_juan_magi_t45():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("BÚSQUEDA: Juan Magi en Torneo 45")
    print("=" * 80)
    
    # Buscar parejas del Torneo 45 con "Magi"
    cur.execute("""
        SELECT tp.id, tp.torneo_id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2,
               tp.jugador1_id, tp.jugador2_id,
               u1.email as email1, u2.email as email2,
               tp.estado, tc.nombre as categoria
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
        LEFT JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
        LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
        WHERE tp.torneo_id = 45
        AND (LOWER(pu1.apellido) LIKE '%magi%' OR LOWER(pu2.apellido) LIKE '%magi%')
        ORDER BY tp.id
    """)
    
    parejas = cur.fetchall()
    
    if parejas:
        print(f"\n📋 Parejas encontradas con 'Magi' en Torneo 45: {len(parejas)}")
        print("-" * 80)
        
        for p in parejas:
            print(f"\nPareja ID {p['id']} - {p['categoria']}")
            print(f"  Jugador 1: {p['jugador1']} (ID {p['jugador1_id']}) - {p['email1']}")
            print(f"  Jugador 2: {p['jugador2']} (ID {p['jugador2_id']}) - {p['email2']}")
            print(f"  Estado: {p['estado']}")
    else:
        print("\n❌ No se encontraron parejas con 'Magi' en Torneo 45")
    
    # Buscar también en partidos del Torneo 45
    print("\n" + "=" * 80)
    print("BÚSQUEDA: Partidos con 'Magi' en Torneo 45")
    print("=" * 80)
    
    cur.execute("""
        SELECT p.id, p.fecha_hora, p.cancha_id, tc.nombre as cancha,
               pu1.nombre || ' ' || pu1.apellido as jugador1_p1,
               pu2.nombre || ' ' || pu2.apellido as jugador2_p1,
               pu3.nombre || ' ' || pu3.apellido as jugador1_p2,
               pu4.nombre || ' ' || pu4.apellido as jugador2_p2,
               tcat.nombre as categoria, tz.nombre as zona
        FROM torneo_partidos p
        LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        LEFT JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        LEFT JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        LEFT JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
        LEFT JOIN torneo_categorias tcat ON p.categoria_id = tcat.id
        LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
        WHERE p.torneo_id = 45
        AND (
            LOWER(pu1.apellido) LIKE '%magi%' OR 
            LOWER(pu2.apellido) LIKE '%magi%' OR
            LOWER(pu3.apellido) LIKE '%magi%' OR
            LOWER(pu4.apellido) LIKE '%magi%'
        )
        ORDER BY p.id
    """)
    
    partidos = cur.fetchall()
    
    if partidos:
        print(f"\n📋 Partidos encontrados: {len(partidos)}")
        print("-" * 80)
        
        for p in partidos:
            print(f"\nPartido ID {p['id']} - {p['categoria']} - {p['zona']}")
            print(f"  {p['jugador1_p1']} / {p['jugador2_p1']}")
            print(f"  vs")
            print(f"  {p['jugador1_p2']} / {p['jugador2_p2']}")
            print(f"  {p['fecha_hora']} - {p['cancha']}")
    else:
        print("\n❌ No se encontraron partidos con 'Magi' en Torneo 45")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    buscar_juan_magi_t45()
