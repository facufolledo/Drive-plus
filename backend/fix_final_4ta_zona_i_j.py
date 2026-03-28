import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def fix_final_4ta():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("FIX FINAL: Zona I y J de 4ta - Torneo 45")
    print("=" * 80)
    
    # 1. Migrar Juan Magui (865) a Juan Magi (562)
    print("\n1️⃣ Migrando Juan Magui (ID 865) a Juan Magi (ID 562)...")
    
    # Verificar parejas de Juan Magui (865)
    cur.execute("""
        SELECT id, jugador1_id, jugador2_id
        FROM torneos_parejas
        WHERE (jugador1_id = 865 OR jugador2_id = 865) AND torneo_id = 45
    """)
    parejas_magui = cur.fetchall()
    
    if parejas_magui:
        for p in parejas_magui:
            if p['jugador1_id'] == 865:
                cur.execute("""
                    UPDATE torneos_parejas
                    SET jugador1_id = 562
                    WHERE id = %s
                """, (p['id'],))
                print(f"   ✅ Pareja {p['id']}: jugador1 migrado de 865 a 562")
            elif p['jugador2_id'] == 865:
                cur.execute("""
                    UPDATE torneos_parejas
                    SET jugador2_id = 562
                    WHERE id = %s
                """, (p['id'],))
                print(f"   ✅ Pareja {p['id']}: jugador2 migrado de 865 a 562")
    else:
        print("   ℹ️  No se encontraron parejas con Juan Magui (865)")
    
    # 2. Corregir pareja 993: FARRUCO -> Pablo Ferreyra (866)
    print("\n2️⃣ Corrigiendo pareja 993: FARRUCO -> Pablo Ferreyra (866)...")
    
    cur.execute("""
        SELECT id, jugador1_id, jugador2_id
        FROM torneos_parejas
        WHERE id = 993
    """)
    pareja_993 = cur.fetchone()
    
    if pareja_993:
        # Buscar ID de FARRUCO
        cur.execute("""
            SELECT u.id_usuario, p.nombre, p.apellido
            FROM usuarios u
            JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.nombre) = 'farruco' OR LOWER(p.apellido) = 'farruco'
        """)
        farruco = cur.fetchone()
        
        if farruco:
            print(f"   📋 FARRUCO encontrado: ID {farruco['id_usuario']} - {farruco['nombre']} {farruco['apellido']}")
            
            # Actualizar jugador2 de la pareja 993
            if pareja_993['jugador2_id'] == farruco['id_usuario']:
                cur.execute("""
                    UPDATE torneos_parejas
                    SET jugador2_id = 866
                    WHERE id = 993
                """)
                print(f"   ✅ Pareja 993: jugador2 actualizado de {farruco['id_usuario']} a 866 (Pablo Ferreyra)")
            elif pareja_993['jugador1_id'] == farruco['id_usuario']:
                cur.execute("""
                    UPDATE torneos_parejas
                    SET jugador1_id = 866
                    WHERE id = 993
                """)
                print(f"   ✅ Pareja 993: jugador1 actualizado de {farruco['id_usuario']} a 866 (Pablo Ferreyra)")
        else:
            print("   ⚠️  No se encontró usuario FARRUCO")
    
    # 3. Crear usuario "Desconocido 2" y actualizar partido 1021
    print("\n3️⃣ Creando 'Desconocido 2' y actualizando partido 1021...")
    
    # Verificar si ya existe Desconocido 2
    cur.execute("""
        SELECT u.id_usuario
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE p.nombre = 'Desconocido' AND p.apellido = '2'
    """)
    desc2 = cur.fetchone()
    
    if not desc2:
        # Crear usuario Desconocido 2
        cur.execute("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, partidos_jugados)
            VALUES ('desconocido2_temp', 'desconocido2@driveplus.temp', 'temp_hash', 1200, 0)
            RETURNING id_usuario
        """)
        desc2_id = cur.fetchone()['id_usuario']
        
        cur.execute("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
            VALUES (%s, 'Desconocido', '2')
        """, (desc2_id,))
        
        print(f"   ✅ Usuario 'Desconocido 2' creado con ID {desc2_id}")
    else:
        desc2_id = desc2['id_usuario']
        print(f"   ℹ️  Usuario 'Desconocido 2' ya existe con ID {desc2_id}")
    
    # Buscar pareja de Alan Corona en partido 1021
    cur.execute("""
        SELECT p.id, p.pareja1_id, p.pareja2_id,
               tp1.jugador1_id as p1_j1, tp1.jugador2_id as p1_j2,
               tp2.jugador1_id as p2_j1, tp2.jugador2_id as p2_j2,
               pu1.nombre || ' ' || pu1.apellido as j1_p1,
               pu2.nombre || ' ' || pu2.apellido as j2_p1,
               pu3.nombre || ' ' || pu3.apellido as j1_p2,
               pu4.nombre || ' ' || pu4.apellido as j2_p2
        FROM torneo_partidos p
        LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        LEFT JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        LEFT JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        LEFT JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id = 1021
    """)
    partido = cur.fetchone()
    
    if partido:
        print(f"\n   📋 Partido 1021:")
        print(f"      Pareja 1: {partido['j1_p1']} / {partido['j2_p1']}")
        print(f"      Pareja 2: {partido['j1_p2']} / {partido['j2_p2']}")
        
        # Buscar ID de Cassiel Lucero
        cur.execute("""
            SELECT u.id_usuario
            FROM usuarios u
            JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.nombre) LIKE '%cassiel%' AND LOWER(p.apellido) LIKE '%lucero%'
        """)
        cassiel = cur.fetchone()
        
        if cassiel:
            cassiel_id = cassiel['id_usuario']
            print(f"   📋 Cassiel Lucero encontrado: ID {cassiel_id}")
            
            # Determinar en qué pareja está Cassiel y actualizarla
            pareja_a_actualizar = None
            jugador_campo = None
            
            if partido['p1_j1'] == cassiel_id:
                pareja_a_actualizar = partido['pareja1_id']
                jugador_campo = 'jugador1_id'
            elif partido['p1_j2'] == cassiel_id:
                pareja_a_actualizar = partido['pareja1_id']
                jugador_campo = 'jugador2_id'
            elif partido['p2_j1'] == cassiel_id:
                pareja_a_actualizar = partido['pareja2_id']
                jugador_campo = 'jugador1_id'
            elif partido['p2_j2'] == cassiel_id:
                pareja_a_actualizar = partido['pareja2_id']
                jugador_campo = 'jugador2_id'
            
            if pareja_a_actualizar and jugador_campo:
                cur.execute(f"""
                    UPDATE torneos_parejas
                    SET {jugador_campo} = %s
                    WHERE id = %s
                """, (desc2_id, pareja_a_actualizar))
                print(f"   ✅ Pareja {pareja_a_actualizar}: {jugador_campo} actualizado a Desconocido 2 (ID {desc2_id})")
            else:
                print("   ⚠️  No se pudo determinar dónde está Cassiel Lucero en el partido")
        else:
            print("   ⚠️  No se encontró usuario Cassiel Lucero")
    
    conn.commit()
    
    # Verificación final
    print("\n" + "=" * 80)
    print("VERIFICACIÓN FINAL")
    print("=" * 80)
    
    # Verificar pareja 993
    cur.execute("""
        SELECT tp.id,
               pu1.nombre || ' ' || pu1.apellido as jugador1,
               pu2.nombre || ' ' || pu2.apellido as jugador2
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
        WHERE tp.id = 993
    """)
    p993 = cur.fetchone()
    
    if p993:
        print(f"\n✅ Pareja 993: {p993['jugador1']} / {p993['jugador2']}")
    
    # Verificar partido 1021
    cur.execute("""
        SELECT p.id,
               pu1.nombre || ' ' || pu1.apellido as j1_p1,
               pu2.nombre || ' ' || pu2.apellido as j2_p1,
               pu3.nombre || ' ' || pu3.apellido as j1_p2,
               pu4.nombre || ' ' || pu4.apellido as j2_p2
        FROM torneo_partidos p
        LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        LEFT JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
        LEFT JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
        LEFT JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
        WHERE p.id = 1021
    """)
    p1021 = cur.fetchone()
    
    if p1021:
        print(f"\n✅ Partido 1021:")
        print(f"   {p1021['j1_p1']} / {p1021['j2_p1']}")
        print(f"   vs")
        print(f"   {p1021['j1_p2']} / {p1021['j2_p2']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CORRECCIONES COMPLETADAS")
    print("=" * 80)

if __name__ == "__main__":
    fix_final_4ta()
