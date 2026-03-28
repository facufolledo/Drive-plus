import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("MIGRACIONES PROPUESTAS - DETALLE COMPLETO")
print("=" * 80)

migraciones = [
    {"id_viejo": 175, "id_nuevo": 1105},
    {"id_viejo": 1102, "id_nuevo": 1104},
    {"id_viejo": 1154, "id_nuevo": 1162}
]

for i, mig in enumerate(migraciones, 1):
    print(f"\n{'=' * 80}")
    print(f"MIGRACIÓN {i}")
    print("=" * 80)
    
    # Usuario VIEJO/TEMP
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
    """, (mig['id_viejo'],))
    
    viejo = cur.fetchone()
    
    print(f"\n🔴 USUARIO VIEJO/TEMP (ID {mig['id_viejo']}):")
    if viejo:
        print(f"   Nombre: {viejo['nombre']} {viejo['apellido']}")
        print(f"   Username: {viejo['nombre_usuario']}")
        print(f"   Email: {viejo['email']}")
        
        # Ver parejas en T46
        cur.execute("""
            SELECT 
                tp.id,
                CASE 
                    WHEN tp.jugador1_id = %s THEN pu2.nombre || ' ' || pu2.apellido
                    ELSE pu1.nombre || ' ' || pu1.apellido
                END as compañero
            FROM torneos_parejas tp
            LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE (tp.jugador1_id = %s OR tp.jugador2_id = %s)
            AND tp.torneo_id = 46
        """, (mig['id_viejo'], mig['id_viejo'], mig['id_viejo']))
        
        parejas = cur.fetchall()
        if parejas:
            print(f"   Parejas en T46:")
            for p in parejas:
                print(f"     - Pareja {p['id']}: con {p['compañero']}")
    else:
        print(f"   ⚠️  No encontrado")
    
    # Usuario NUEVO/REGISTRADO
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
    """, (mig['id_nuevo'],))
    
    nuevo = cur.fetchone()
    
    print(f"\n🟢 USUARIO NUEVO/REGISTRADO (ID {mig['id_nuevo']}):")
    if nuevo:
        print(f"   Nombre: {nuevo['nombre']} {nuevo['apellido']}")
        print(f"   Username: {nuevo['nombre_usuario']}")
        print(f"   Email: {nuevo['email']}")
        
        # Ver parejas en T46
        cur.execute("""
            SELECT 
                tp.id,
                CASE 
                    WHEN tp.jugador1_id = %s THEN pu2.nombre || ' ' || pu2.apellido
                    ELSE pu1.nombre || ' ' || pu1.apellido
                END as compañero
            FROM torneos_parejas tp
            LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
            LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
            WHERE (tp.jugador1_id = %s OR tp.jugador2_id = %s)
            AND tp.torneo_id = 46
        """, (mig['id_nuevo'], mig['id_nuevo'], mig['id_nuevo']))
        
        parejas = cur.fetchall()
        if parejas:
            print(f"   Parejas en T46:")
            for p in parejas:
                print(f"     - Pareja {p['id']}: con {p['compañero']}")
        else:
            print(f"   Sin parejas en T46 (aún)")
    else:
        print(f"   ⚠️  No encontrado")
    
    print(f"\n➡️  ACCIÓN: Migrar todas las parejas, partidos e historial de {mig['id_viejo']} → {mig['id_nuevo']}")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)
print("\nEstas migraciones van a:")
print("  1. Actualizar torneos_parejas para que usen el ID nuevo")
print("  2. Actualizar historial_rating para que use el ID nuevo")
print("  3. Eliminar el usuario viejo/temp")

cur.close()
conn.close()
