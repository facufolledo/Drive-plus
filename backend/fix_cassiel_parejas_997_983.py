import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def fix_cassiel_parejas():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print("=" * 80)
    print("FIX: Reemplazar Cassiel Lucero en parejas 997 y 983")
    print("=" * 80)
    
    cassiel_id = 1
    desc2_id = 1015
    
    # Verificar si Desconocido 3 existe
    cur.execute("""
        SELECT id_usuario
        FROM perfil_usuarios
        WHERE nombre = 'Desconocido' AND apellido = '3'
    """)
    desc3 = cur.fetchone()
    
    if not desc3:
        # Crear Desconocido 3
        cur.execute("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, partidos_jugados)
            VALUES ('desconocido3_temp', 'desconocido3@driveplus.temp', 'temp_hash', 1200, 0)
            RETURNING id_usuario
        """)
        desc3_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
            VALUES (%s, 'Desconocido', '3')
        """, (desc3_id,))
        
        print(f"\n✅ Usuario 'Desconocido 3' creado: ID {desc3_id}")
    else:
        desc3_id = desc3[0]
        print(f"\n✅ Usuario 'Desconocido 3' ya existe: ID {desc3_id}")
    
    # Pareja 997 (Zona J): Alan Corona / Cassiel → Alan Corona / Desconocido 2
    print(f"\n📋 Pareja 997 (Zona J):")
    print(f"   Reemplazando Cassiel (ID {cassiel_id}) por Desconocido 2 (ID {desc2_id})")
    
    cur.execute("""
        UPDATE torneos_parejas
        SET jugador2_id = %s
        WHERE id = 997 AND jugador2_id = %s
    """, (desc2_id, cassiel_id))
    
    print(f"   ✅ Actualizado: Alan Corona / Desconocido 2")
    
    # Pareja 983 (Zona E): Joaquin Coppede / Cassiel → Joaquin Coppede / Desconocido 3
    print(f"\n📋 Pareja 983 (Zona E):")
    print(f"   Reemplazando Cassiel (ID {cassiel_id}) por Desconocido 3 (ID {desc3_id})")
    
    cur.execute("""
        UPDATE torneos_parejas
        SET jugador2_id = %s
        WHERE id = 983 AND jugador2_id = %s
    """, (desc3_id, cassiel_id))
    
    print(f"   ✅ Actualizado: Joaquin Coppede / Desconocido 3")
    
    conn.commit()
    
    # Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL")
    print("=" * 80)
    
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
        WHERE tp.id IN (997, 983)
        ORDER BY tp.id
    """)
    
    parejas = cur.fetchall()
    
    for p in parejas:
        print(f"\n✅ Pareja {p[0]} - {p[3]}: {p[1]} / {p[2]}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CORRECCIONES COMPLETADAS")
    print("=" * 80)

if __name__ == "__main__":
    fix_cassiel_parejas()
