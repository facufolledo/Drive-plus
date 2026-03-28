import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def fix_millicay():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("FIX: Millicay en Zona A - 8va")
    print("=" * 80)
    
    # Buscar Zona A de 8va
    cur.execute("""
        SELECT tz.id, tz.nombre, tc.nombre as categoria
        FROM torneo_zonas tz
        LEFT JOIN torneo_categorias tc ON tz.categoria_id = tc.id
        WHERE tz.torneo_id = 45
        AND tz.nombre = 'Zona A'
        AND tc.nombre = '8va'
    """)
    zona = cur.fetchone()
    
    if not zona:
        print("❌ No se encontró Zona A de 8va")
        cur.close()
        conn.close()
        return
    
    print(f"\n✅ Zona encontrada: {zona['nombre']} - {zona['categoria']} (ID {zona['id']})")
    
    # Buscar parejas de la zona
    cur.execute("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneo_zona_parejas tzp
        JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tzp.zona_id = %s
    """, (zona['id'],))
    
    parejas = cur.fetchall()
    
    print(f"\n📋 Parejas en Zona A - 8va:")
    for p in parejas:
        print(f"   Pareja {p['id']}: {p['jugador1']} / {p['jugador2']}")
    
    # Buscar usuarios con apellido Millicay
    cur.execute("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.apellido) LIKE '%millicay%'
    """)
    millicays = cur.fetchall()
    
    print(f"\n📋 Usuarios con apellido Millicay: {len(millicays)}")
    for m in millicays:
        print(f"   ID {m['id_usuario']}: {m['nombre']} {m['apellido']} - {m['email']}")
    
    # Buscar el Millicay que NO es Gustavo
    millicay_correcto = None
    for m in millicays:
        if m['nombre'] and 'gustavo' not in m['nombre'].lower():
            millicay_correcto = m
            break
    
    if millicay_correcto:
        print(f"\n✅ Millicay encontrado (no Gustavo): ID {millicay_correcto['id_usuario']}")
        print(f"   Nombre actual: {millicay_correcto['nombre']} {millicay_correcto['apellido']}")
        
        # Verificar si tiene perfil
        if millicay_correcto['nombre']:
            # Actualizar perfil
            cur.execute("""
                UPDATE perfil_usuarios
                SET nombre = 'Pant', apellido = 'Millicay'
                WHERE id_usuario = %s
            """, (millicay_correcto['id_usuario'],))
            print(f"   ✅ Perfil actualizado: Pant Millicay")
        else:
            # Crear perfil
            cur.execute("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                VALUES (%s, 'Pant', 'Millicay')
            """, (millicay_correcto['id_usuario'],))
            print(f"   ✅ Perfil creado: Pant Millicay")
    else:
        print("\n⚠️  No se encontró un Millicay que no sea Gustavo")
        
        # Buscar en las parejas de la zona si hay algún usuario sin nombre correcto
        for p in parejas:
            # Verificar jugador1
            cur.execute("""
                SELECT u.id_usuario, p.nombre, p.apellido
                FROM usuarios u
                LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
                WHERE u.id_usuario = %s
            """, (p['jugador1_id'],))
            j1 = cur.fetchone()
            
            if j1 and j1['apellido'] and 'millicay' in j1['apellido'].lower() and (not j1['nombre'] or 'gustavo' not in j1['nombre'].lower()):
                print(f"\n✅ Encontrado en pareja {p['id']} - jugador1 (ID {j1['id_usuario']})")
                
                if j1['nombre']:
                    cur.execute("""
                        UPDATE perfil_usuarios
                        SET nombre = 'Pant', apellido = 'Millicay'
                        WHERE id_usuario = %s
                    """, (j1['id_usuario'],))
                    print(f"   ✅ Perfil actualizado: Pant Millicay")
                else:
                    cur.execute("""
                        INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                        VALUES (%s, 'Pant', 'Millicay')
                    """, (j1['id_usuario'],))
                    print(f"   ✅ Perfil creado: Pant Millicay")
                break
            
            # Verificar jugador2
            cur.execute("""
                SELECT u.id_usuario, p.nombre, p.apellido
                FROM usuarios u
                LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
                WHERE u.id_usuario = %s
            """, (p['jugador2_id'],))
            j2 = cur.fetchone()
            
            if j2 and j2['apellido'] and 'millicay' in j2['apellido'].lower() and (not j2['nombre'] or 'gustavo' not in j2['nombre'].lower()):
                print(f"\n✅ Encontrado en pareja {p['id']} - jugador2 (ID {j2['id_usuario']})")
                
                if j2['nombre']:
                    cur.execute("""
                        UPDATE perfil_usuarios
                        SET nombre = 'Pant', apellido = 'Millicay'
                        WHERE id_usuario = %s
                    """, (j2['id_usuario'],))
                    print(f"   ✅ Perfil actualizado: Pant Millicay")
                else:
                    cur.execute("""
                        INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                        VALUES (%s, 'Pant', 'Millicay')
                    """, (j2['id_usuario'],))
                    print(f"   ✅ Perfil creado: Pant Millicay")
                break
    
    conn.commit()
    
    # Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL - Zona A - 8va")
    print("=" * 80)
    
    cur.execute("""
        SELECT tp.id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneo_zona_parejas tzp
        JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tzp.zona_id = %s
        ORDER BY tp.id
    """, (zona['id'],))
    
    parejas_final = cur.fetchall()
    
    for p in parejas_final:
        print(f"\n✅ Pareja {p['id']}: {p['jugador1']} / {p['jugador2']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CORRECCIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    fix_millicay()
