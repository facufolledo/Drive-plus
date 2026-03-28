import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def verificar_correcciones():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("VERIFICACIÓN FINAL: Correcciones Torneo 45")
    print("=" * 80)
    
    # 1. Verificar pareja 993 (Zona I de 4ta)
    print("\n1️⃣ Pareja 993 (Zona I - 4ta):")
    cur.execute("""
        SELECT tp.id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2,
               tz.nombre as zona,
               tc.nombre as categoria
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        LEFT JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
        LEFT JOIN torneo_zonas tz ON tzp.zona_id = tz.id
        LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
        WHERE tp.id = 993
    """)
    p993 = cur.fetchone()
    
    if p993:
        print(f"   ✅ {p993['jugador1']} / {p993['jugador2']}")
        print(f"   📍 {p993['zona']} - {p993['categoria']}")
    
    # 2. Verificar pareja 994 (Juan Magi)
    print("\n2️⃣ Pareja 994 (Juan Magi):")
    cur.execute("""
        SELECT tp.id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2,
               tp.jugador1_id, tp.jugador2_id
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id = 994
    """)
    p994 = cur.fetchone()
    
    if p994:
        print(f"   ✅ {p994['jugador1']} (ID {p994['jugador1_id']}) / {p994['jugador2']} (ID {p994['jugador2_id']})")
    
    # 3. Verificar partido 1021 (Alan Corona)
    print("\n3️⃣ Partido 1021 (Zona J - 4ta):")
    cur.execute("""
        SELECT p.id,
               pu1.nombre || ' ' || pu1.apellido as j1_p1,
               pu2.nombre || ' ' || pu2.apellido as j2_p1,
               pu3.nombre || ' ' || pu3.apellido as j1_p2,
               pu4.nombre || ' ' || pu4.apellido as j2_p2,
               p.fecha_hora, tc.nombre as cancha
        FROM torneo_partidos p
        LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        LEFT JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        LEFT JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        LEFT JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id = 1021
    """)
    p1021 = cur.fetchone()
    
    if p1021:
        print(f"   {p1021['j1_p1']} / {p1021['j2_p1']}")
        print(f"   vs")
        print(f"   {p1021['j1_p2']} / {p1021['j2_p2']}")
        print(f"   📅 {p1021['fecha_hora']} - {p1021['cancha']}")
    
    # 4. Verificar todos los partidos de Zona I y J de 4ta
    print("\n" + "=" * 80)
    print("PARTIDOS ZONA I y J - 4ta")
    print("=" * 80)
    
    cur.execute("""
        SELECT p.id,
               pu1.nombre || ' ' || pu1.apellido as j1_p1,
               pu2.nombre || ' ' || pu2.apellido as j2_p1,
               pu3.nombre || ' ' || pu3.apellido as j1_p2,
               pu4.nombre || ' ' || pu4.apellido as j2_p2,
               tz.nombre as zona,
               p.fecha_hora, tca.nombre as cancha
        FROM torneo_partidos p
        LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        LEFT JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        LEFT JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        LEFT JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
        LEFT JOIN torneo_canchas tca ON p.cancha_id = tca.id
        WHERE p.torneo_id = 45 
        AND tz.nombre IN ('Zona I', 'Zona J')
        AND tz.categoria_id = (SELECT id FROM torneo_categorias WHERE torneo_id = 45 AND nombre = '4ta')
        ORDER BY tz.nombre, p.fecha_hora
    """)
    partidos = cur.fetchall()
    
    zona_actual = None
    for partido in partidos:
        if partido['zona'] != zona_actual:
            zona_actual = partido['zona']
            print(f"\n{zona_actual}:")
        
        print(f"  Partido {partido['id']}:")
        print(f"    {partido['j1_p1']} / {partido['j2_p1']}")
        print(f"    vs")
        print(f"    {partido['j1_p2']} / {partido['j2_p2']}")
        print(f"    📅 {partido['fecha_hora']} - {partido['cancha']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    verificar_correcciones()
