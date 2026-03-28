import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR USUARIOS REGISTRADOS")
print("=" * 80)

usuarios_registrados = [1105, 1104, 1156, 1162]

for user_id in usuarios_registrados:
    print(f"\n{'=' * 80}")
    print(f"USUARIO ID {user_id}")
    print("=" * 80)
    
    # Ver datos del usuario
    cur.execute("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            u.email,
            pu.nombre,
            pu.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
        WHERE u.id_usuario = %s
    """, (user_id,))
    
    usuario = cur.fetchone()
    
    if usuario:
        print(f"\n✓ Usuario encontrado:")
        print(f"  ID: {usuario['id_usuario']}")
        print(f"  Username: {usuario['nombre_usuario']}")
        print(f"  Email: {usuario['email']}")
        print(f"  Nombre: {usuario['nombre']} {usuario['apellido']}")
        
        # Buscar si hay un temp con nombre similar
        nombre_completo = f"{usuario['nombre']} {usuario['apellido']}".lower()
        
        cur.execute("""
            SELECT 
                u.id_usuario,
                u.nombre_usuario,
                u.email,
                pu.nombre,
                pu.apellido
            FROM usuarios u
            JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE u.id_usuario != %s
            AND (
                LOWER(pu.nombre || ' ' || pu.apellido) LIKE %s
                OR LOWER(pu.apellido || ' ' || pu.nombre) LIKE %s
                OR (LOWER(pu.apellido) = LOWER(%s) AND LOWER(pu.nombre) LIKE %s)
            )
            AND (u.email LIKE '%%@temp.com' OR u.email LIKE '%%@example.com')
        """, (user_id, f"%{usuario['apellido'].lower()}%", f"%{usuario['apellido'].lower()}%", 
              usuario['apellido'], f"%{usuario['nombre'].lower()[:3]}%"))
        
        temps_similares = cur.fetchall()
        
        if temps_similares:
            print(f"\n  ⚠️  POSIBLES TEMPS DUPLICADOS:")
            for temp in temps_similares:
                print(f"\n    ID {temp['id_usuario']}: {temp['nombre']} {temp['apellido']}")
                print(f"      Username: {temp['nombre_usuario']}")
                print(f"      Email: {temp['email']}")
                
                # Ver si tiene parejas en torneo 46
                cur.execute("""
                    SELECT 
                        tp.id as pareja_id,
                        tp.torneo_id,
                        pu2.nombre || ' ' || pu2.apellido as compañero
                    FROM torneos_parejas tp
                    LEFT JOIN perfil_usuarios pu2 ON (
                        CASE 
                            WHEN tp.jugador1_id = %s THEN tp.jugador2_id
                            ELSE tp.jugador1_id
                        END = pu2.id_usuario
                    )
                    WHERE (tp.jugador1_id = %s OR tp.jugador2_id = %s)
                    AND tp.torneo_id = 46
                """, (temp['id_usuario'], temp['id_usuario'], temp['id_usuario']))
                
                parejas_temp = cur.fetchall()
                
                if parejas_temp:
                    print(f"      Parejas en T46:")
                    for p in parejas_temp:
                        print(f"        - Pareja {p['pareja_id']}: con {p['compañero']}")
                else:
                    print(f"      Sin parejas en T46")
                
                # Ver partidos
                cur.execute("""
                    SELECT COUNT(*) as total
                    FROM partidos p
                    JOIN torneos_parejas tp ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
                    WHERE (tp.jugador1_id = %s OR tp.jugador2_id = %s)
                    AND p.id_torneo = 46
                """, (temp['id_usuario'], temp['id_usuario']))
                
                partidos_count = cur.fetchone()
                print(f"      Partidos en T46: {partidos_count['total']}")
        else:
            print(f"\n  ✓ No se encontraron temps similares")
    else:
        print(f"\n⚠️  Usuario {user_id} no encontrado")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)

print("\nSi encontramos temps duplicados, necesitamos:")
print("  1. Actualizar torneos_parejas: cambiar jugador_temp por jugador_real")
print("  2. Actualizar historial_rating: cambiar id_usuario_temp por id_usuario_real")
print("  3. Actualizar restricciones_horarias_parejas: cambiar id_usuario_temp por id_usuario_real")
print("  4. Eliminar el usuario temp")

cur.close()
conn.close()
