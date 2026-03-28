import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def debug_partido_1021():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("DEBUG: Partido 1021")
    print("=" * 80)
    
    # Verificar si existe el partido
    cur.execute("""
        SELECT p.id, p.torneo_id, p.pareja1_id, p.pareja2_id, p.zona_id,
               p.fecha_hora, p.cancha_id
        FROM torneo_partidos p
        WHERE p.id = 1021
    """)
    partido = cur.fetchone()
    
    if partido:
        print(f"\n✅ Partido 1021 existe:")
        print(f"   Torneo ID: {partido['torneo_id']}")
        print(f"   Pareja 1 ID: {partido['pareja1_id']}")
        print(f"   Pareja 2 ID: {partido['pareja2_id']}")
        print(f"   Zona ID: {partido['zona_id']}")
        print(f"   Fecha/Hora: {partido['fecha_hora']}")
        print(f"   Cancha ID: {partido['cancha_id']}")
        
        # Ver parejas
        if partido['pareja1_id']:
            cur.execute("""
                SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
                       pu1.nombre || ' ' || pu1.apellido as j1,
                       pu2.nombre || ' ' || pu2.apellido as j2
                FROM torneos_parejas tp
                LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
                LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
                WHERE tp.id = %s
            """, (partido['pareja1_id'],))
            p1 = cur.fetchone()
            print(f"\n   Pareja 1: {p1['j1']} / {p1['j2']}")
        
        if partido['pareja2_id']:
            cur.execute("""
                SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
                       pu1.nombre || ' ' || pu1.apellido as j1,
                       pu2.nombre || ' ' || pu2.apellido as j2
                FROM torneos_parejas tp
                LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
                LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
                WHERE tp.id = %s
            """, (partido['pareja2_id'],))
            p2 = cur.fetchone()
            print(f"   Pareja 2: {p2['j1']} / {p2['j2']}")
        
        # Ver zona
        if partido['zona_id']:
            cur.execute("""
                SELECT nombre
                FROM torneo_zonas
                WHERE id = %s
            """, (partido['zona_id'],))
            zona = cur.fetchone()
            print(f"\n   Zona: {zona['nombre']}")
    else:
        print("\n❌ Partido 1021 NO existe")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    debug_partido_1021()
