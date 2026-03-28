import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

try:
    # Obtener IDs
    cur.execute("SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '7ma'")
    categoria_id = cur.fetchone()['id']
    
    cur.execute("SELECT id FROM torneo_zonas WHERE torneo_id = 46 AND categoria_id = %s AND nombre = 'Zona D'", (categoria_id,))
    zona_d_id = cur.fetchone()['id']
    
    print(f"Categoría 7ma: ID {categoria_id}")
    print(f"Zona D: ID {zona_d_id}")
    
    # Pareja sin zona
    pareja_sin_zona = 1005  # Lucas Apostolo / Mariano Roldán
    
    # Parejas actuales en Zona D
    parejas_zona_d = [1016, 1023]  # Diego Bicet/Marcelo Aguilar, Renzo Gonzales/Erik Letterucci
    
    print(f"\n📋 Pareja a agregar: {pareja_sin_zona}")
    print(f"📋 Parejas actuales en Zona D: {parejas_zona_d}")
    
    # Crear los 2 partidos faltantes:
    # 1. Pareja 1005 vs Pareja 1016
    # 2. Pareja 1005 vs Pareja 1023
    
    partidos_a_crear = [
        (pareja_sin_zona, parejas_zona_d[0]),  # 1005 vs 1016
        (pareja_sin_zona, parejas_zona_d[1])   # 1005 vs 1023
    ]
    
    print("\n🔨 Creando partidos faltantes:")
    
    for p1_id, p2_id in partidos_a_crear:
        # Obtener nombres
        cur.execute("""
            SELECT 
                pu1.nombre || ' ' || pu1.apellido as j1,
                pu2.nombre || ' ' || pu2.apellido as j2
            FROM torneos_parejas tp
            JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tp.id = %s
        """, (p1_id,))
        p1 = cur.fetchone()
        
        cur.execute("""
            SELECT 
                pu1.nombre || ' ' || pu1.apellido as j1,
                pu2.nombre || ' ' || pu2.apellido as j2
            FROM torneos_parejas tp
            JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE tp.id = %s
        """, (p2_id,))
        p2 = cur.fetchone()
        
        # Crear partido
        cur.execute("""
            INSERT INTO partidos (
                id_torneo, categoria_id, zona_id,
                pareja1_id, pareja2_id,
                fase, estado, fecha, id_creador
            ) VALUES (
                %s, %s, %s,
                %s, %s,
                'zona', 'pendiente', NOW(), 1
            )
            RETURNING id_partido
        """, (46, categoria_id, zona_d_id, p1_id, p2_id))
        
        partido_id = cur.fetchone()['id_partido']
        print(f"  ✅ Partido {partido_id}: P{p1_id} ({p1['j1']}/{p1['j2']}) vs P{p2_id} ({p2['j1']}/{p2['j2']})")
    
    conn.commit()
    
    # Verificar resultado final
    cur.execute("""
        SELECT COUNT(*) as total
        FROM partidos
        WHERE id_torneo = 46 AND categoria_id = %s AND zona_id = %s
    """, (categoria_id, zona_d_id))
    
    total_partidos = cur.fetchone()['total']
    
    print(f"\n🎉 ZONA D COMPLETADA:")
    print(f"   - 3 parejas")
    print(f"   - {total_partidos} partidos (todos contra todos)")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
