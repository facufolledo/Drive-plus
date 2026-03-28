import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def fix_cassiel_y_jugadores():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("FIX: Cassiel Lucero y Jugadores 886/887 en 6ta")
    print("=" * 80)
    
    # 1. Buscar Cassiel Lucero
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.nombre) LIKE '%cassiel%' AND LOWER(p.apellido) LIKE '%lucero%'
    """)
    cassiel = cur.fetchone()
    
    if cassiel:
        cassiel_id = cassiel['id_usuario']
        print(f"\n📋 Cassiel Lucero encontrado: ID {cassiel_id}")
        
        # Buscar parejas de Cassiel en Torneo 45
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
            AND tc.nombre = '6ta'
        """, (cassiel_id, cassiel_id))
        
        parejas_cassiel = cur.fetchall()
        
        if parejas_cassiel:
            print(f"\n📋 Parejas de Cassiel en 6ta:")
            for p in parejas_cassiel:
                print(f"   Pareja {p['id']} - {p['zona']}: {p['jugador1']} / {p['jugador2']}")
            
            # Crear Desconocido 3
            cur.execute("""
                SELECT u.id_usuario
                FROM usuarios u
                JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
                WHERE p.nombre = 'Desconocido' AND p.apellido = '3'
            """)
            desc3 = cur.fetchone()
            
            if not desc3:
                cur.execute("""
                    INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, partidos_jugados)
                    VALUES ('desconocido3_temp', 'desconocido3@driveplus.temp', 'temp_hash', 1200, 0)
                    RETURNING id_usuario
                """)
                desc3_id = cur.fetchone()['id_usuario']
                
                cur.execute("""
                    INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                    VALUES (%s, 'Desconocido', '3')
                """, (desc3_id,))
                
                print(f"\n✅ Usuario 'Desconocido 3' creado: ID {desc3_id}")
            else:
                desc3_id = desc3['id_usuario']
                print(f"\n✅ Usuario 'Desconocido 3' ya existe: ID {desc3_id}")
            
            # Reemplazar Cassiel por Desconocido 3
            for p in parejas_cassiel:
                if p['jugador1_id'] == cassiel_id:
                    cur.execute("""
                        UPDATE torneos_parejas
                        SET jugador1_id = %s
                        WHERE id = %s
                    """, (desc3_id, p['id']))
                    print(f"   ✅ Pareja {p['id']}: jugador1 actualizado (Cassiel → Desconocido 3)")
                elif p['jugador2_id'] == cassiel_id:
                    cur.execute("""
                        UPDATE torneos_parejas
                        SET jugador2_id = %s
                        WHERE id = %s
                    """, (desc3_id, p['id']))
                    print(f"   ✅ Pareja {p['id']}: jugador2 actualizado (Cassiel → Desconocido 3)")
    
    # 2. Buscar usuarios "Jugador 886" y "Jugador 887"
    print("\n" + "=" * 80)
    print("FIX: Jugador 886 y 887 → Aguero Ale y Lois Hoga")
    print("=" * 80)
    
    cur.execute("""
        SELECT u.id_usuario, u.nombre_usuario, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.id_usuario IN (886, 887)
        ORDER BY u.id_usuario
    """)
    jugadores = cur.fetchall()
    
    for j in jugadores:
        print(f"\n📋 Usuario ID {j['id_usuario']}: {j['nombre']} {j['apellido']}")
        
        if j['id_usuario'] == 886:
            # Crear/actualizar perfil para Aguero Ale
            if j['nombre']:
                cur.execute("""
                    UPDATE perfil_usuarios
                    SET nombre = 'Aguero', apellido = 'Ale'
                    WHERE id_usuario = 886
                """)
                print(f"   ✅ Perfil actualizado: Aguero Ale")
            else:
                cur.execute("""
                    INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                    VALUES (886, 'Aguero', 'Ale')
                """)
                print(f"   ✅ Perfil creado: Aguero Ale")
        
        elif j['id_usuario'] == 887:
            # Crear/actualizar perfil para Lois Hoga
            if j['nombre']:
                cur.execute("""
                    UPDATE perfil_usuarios
                    SET nombre = 'Lois', apellido = 'Hoga'
                    WHERE id_usuario = 887
                """)
                print(f"   ✅ Perfil actualizado: Lois Hoga")
            else:
                cur.execute("""
                    INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                    VALUES (887, 'Lois', 'Hoga')
                """)
                print(f"   ✅ Perfil creado: Lois Hoga")
    
    conn.commit()
    
    # Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL")
    print("=" * 80)
    
    # Verificar parejas de 6ta con Desconocido 3
    if cassiel:
        cur.execute("""
            SELECT tp.id,
                   pu1.nombre || ' ' || pu1.apellido as jugador1,
                   pu2.nombre || ' ' || pu2.apellido as jugador2,
                   tz.nombre as zona
            FROM torneos_parejas tp
            LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            LEFT JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
            LEFT JOIN torneo_zonas tz ON tzp.zona_id = tz.id
            LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
            WHERE tp.torneo_id = 45
            AND (tp.jugador1_id = %s OR tp.jugador2_id = %s)
            AND tc.nombre = '6ta'
        """, (desc3_id, desc3_id))
        
        parejas_desc3 = cur.fetchall()
        
        if parejas_desc3:
            print(f"\n✅ Parejas con Desconocido 3:")
            for p in parejas_desc3:
                print(f"   Pareja {p['id']} - {p['zona']}: {p['jugador1']} / {p['jugador2']}")
    
    # Verificar usuarios 886 y 887
    cur.execute("""
        SELECT u.id_usuario, p.nombre || ' ' || p.apellido as nombre_completo
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.id_usuario IN (886, 887)
        ORDER BY u.id_usuario
    """)
    usuarios_final = cur.fetchall()
    
    print(f"\n✅ Usuarios actualizados:")
    for u in usuarios_final:
        print(f"   ID {u['id_usuario']}: {u['nombre_completo']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CORRECCIONES COMPLETADAS")
    print("=" * 80)

if __name__ == "__main__":
    fix_cassiel_y_jugadores()
