import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def listar_zona_j():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("PARTIDOS ZONA J - 4ta - Torneo 45")
    print("=" * 80)
    
    # Buscar zona J de 4ta
    cur.execute("""
        SELECT tz.id, tz.nombre, tc.nombre as categoria
        FROM torneo_zonas tz
        LEFT JOIN torneo_categorias tc ON tz.categoria_id = tc.id
        WHERE tz.torneo_id = 45
        AND tz.nombre = 'Zona J'
        AND tc.nombre = '4ta'
    """)
    zona = cur.fetchone()
    
    if zona:
        print(f"\n✅ Zona encontrada: {zona['nombre']} - {zona['categoria']} (ID {zona['id']})")
        
        # Listar partidos
        cur.execute("""
            SELECT p.id,
                   pu1.nombre || ' ' || pu1.apellido as j1_p1,
                   pu2.nombre || ' ' || pu2.apellido as j2_p1,
                   pu3.nombre || ' ' || pu3.apellido as j1_p2,
                   pu4.nombre || ' ' || pu4.apellido as j2_p2,
                   p.fecha_hora, tca.nombre as cancha,
                   tp1.jugador1_id as p1_j1_id, tp1.jugador2_id as p1_j2_id,
                   tp2.jugador1_id as p2_j1_id, tp2.jugador2_id as p2_j2_id
            FROM torneo_partidos p
            LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            LEFT JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
            LEFT JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
            LEFT JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
            LEFT JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
            LEFT JOIN torneo_canchas tca ON p.cancha_id = tca.id
            WHERE p.zona_id = %s
            ORDER BY p.fecha_hora
        """, (zona['id'],))
        
        partidos = cur.fetchall()
        
        print(f"\n📋 Partidos encontrados: {len(partidos)}")
        print("-" * 80)
        
        for p in partidos:
            print(f"\nPartido ID {p['id']}:")
            print(f"  {p['j1_p1']} (ID {p['p1_j1_id']}) / {p['j2_p1']} (ID {p['p1_j2_id']})")
            print(f"  vs")
            print(f"  {p['j1_p2']} (ID {p['p2_j1_id']}) / {p['j2_p2']} (ID {p['p2_j2_id']})")
            print(f"  📅 {p['fecha_hora']} - {p['cancha']}")
    else:
        print("\n❌ No se encontró Zona J de 4ta")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    listar_zona_j()
