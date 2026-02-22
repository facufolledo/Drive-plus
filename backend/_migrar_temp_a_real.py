"""Migrar usuarios temp a sus cuentas reales en torneo 38.
Paso 1: Santiago Rodríguez (538->12) y Matías Castelli (539->6)
Paso 2: Buscar todos los demás temp migrables
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def migrar_usuario(c, temp_id, real_id, nombre):
    """Migra un usuario temp a su cuenta real"""
    # 1. Obtener datos del temp
    temp = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :id"), {"id": temp_id}).fetchone()
    real = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :id"), {"id": real_id}).fetchone()
    
    print(f"\n  {nombre}: TEMP ID={temp_id} (rating={temp[0]}, pj={temp[1]}) -> REAL ID={real_id} (rating={real[0]}, pj={real[1]})")
    
    # 2. Actualizar torneos_parejas (jugador1_id o jugador2_id)
    r1 = c.execute(text("UPDATE torneos_parejas SET jugador1_id = :real WHERE jugador1_id = :temp AND torneo_id = 38"), {"real": real_id, "temp": temp_id}).rowcount
    r2 = c.execute(text("UPDATE torneos_parejas SET jugador2_id = :real WHERE jugador2_id = :temp AND torneo_id = 38"), {"real": real_id, "temp": temp_id}).rowcount
    print(f"    torneos_parejas: {r1+r2} actualizadas")
    
    # 3. Actualizar historial_rating
    r3 = c.execute(text("UPDATE historial_rating SET id_usuario = :real WHERE id_usuario = :temp"), {"real": real_id, "temp": temp_id}).rowcount
    print(f"    historial_rating: {r3} registros migrados")
    
    # 4. Actualizar rating y partidos_jugados del usuario real
    c.execute(text("""
        UPDATE usuarios SET rating = :rating, partidos_jugados = partidos_jugados + :pj
        WHERE id_usuario = :real
    """), {"rating": temp[0], "pj": temp[1], "real": real_id})
    print(f"    usuario real: rating={temp[0]}, partidos_jugados+={temp[1]}")
    
    return True

with engine.connect() as c:
    # === PASO 1: Migrar los conocidos ===
    print("=" * 60)
    print("PASO 1: MIGRAR SANTIAGO RODRÍGUEZ Y MATÍAS CASTELLI")
    print("=" * 60)
    
    migrar_usuario(c, 538, 12, "Santiago Rodríguez")
    migrar_usuario(c, 539, 6, "Matías Castelli")
    c.commit()
    print("\n✅ Migrados")

    # === PASO 2: Buscar TODOS los temp del torneo 38 ===
    print("\n" + "=" * 60)
    print("PASO 2: BUSCAR TODOS LOS TEMP DEL TORNEO 38")
    print("=" * 60)
    
    temps = c.execute(text("""
        SELECT DISTINCT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.email LIKE '%@driveplus.temp'
        AND u.id_usuario IN (
            SELECT jugador1_id FROM torneos_parejas WHERE torneo_id = 38
            UNION
            SELECT jugador2_id FROM torneos_parejas WHERE torneo_id = 38
        )
        ORDER BY p.apellido, p.nombre
    """)).fetchall()
    
    print(f"\n  {len(temps)} usuarios temp en torneo 38:")
    migrables = []
    for t in temps:
        # Buscar cuenta real con mismo nombre+apellido
        reales = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido
            FROM usuarios u
            JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.email NOT LIKE '%@driveplus.temp'
            AND LOWER(p.nombre) = LOWER(:nom)
            AND LOWER(p.apellido) = LOWER(:ape)
            AND u.id_usuario != :tid
        """), {"nom": t[3].strip(), "ape": t[4].strip(), "tid": t[0]}).fetchall()
        
        if reales:
            for r in reales:
                print(f"  ✅ {t[3]} {t[4]} TEMP={t[0]} -> REAL={r[0]} ({r[1]})")
                migrables.append((t[0], r[0], f"{t[3]} {t[4]}"))
        else:
            print(f"  ❌ {t[3]} {t[4]} TEMP={t[0]} ({t[1]}) - sin cuenta real")

    # === PASO 3: Migrar los encontrados ===
    if migrables:
        print(f"\n{'=' * 60}")
        print(f"PASO 3: MIGRAR {len(migrables)} USUARIOS")
        print("=" * 60)
        for temp_id, real_id, nombre in migrables:
            migrar_usuario(c, temp_id, real_id, nombre)
        c.commit()
        print(f"\n✅ {len(migrables)} usuarios migrados")
    else:
        print("\n  No hay más migrables")
