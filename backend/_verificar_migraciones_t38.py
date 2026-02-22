"""Verificar estado de migraciones temp->real en torneo 38 y listar pendientes."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # 1. Verificar Ferreyra y Gudiño
    print("=" * 60)
    print("1. VERIFICAR FERREYRA Y GUDIÑO")
    print("=" * 60)
    for uid, nombre in [(84, "Pablo Ferreyra"), (67, "Carlos Gudiño")]:
        u = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
        # Verificar en qué parejas están
        parejas = c.execute(text("""
            SELECT tp.id, tp.torneo_id, tcat.nombre as cat, tp.jugador1_id, tp.jugador2_id
            FROM torneos_parejas tp
            JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
            WHERE (tp.jugador1_id = :uid OR tp.jugador2_id = :uid) AND tp.torneo_id = 38
        """), {"uid": uid}).fetchall()
        print(f"  {nombre} (ID {uid}): rating={u[0]}, pj={u[1]}")
        for p in parejas:
            print(f"    Pareja {p[0]} en {p[2]} (j1={p[3]}, j2={p[4]})")

    # 2. Verificar Santiago Rodríguez y Matías Castelli
    print(f"\n{'=' * 60}")
    print("2. VERIFICAR SANTIAGO RODRÍGUEZ Y MATÍAS CASTELLI")
    print("=" * 60)
    for uid, nombre in [(12, "Santiago Rodríguez"), (6, "Matías Castelli")]:
        u = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
        hr = c.execute(text("""
            SELECT hr.id_partido, p.tipo, hr.rating_antes, hr.delta, hr.rating_despues
            FROM historial_rating hr
            JOIN partidos p ON hr.id_partido = p.id_partido
            WHERE hr.id_usuario = :uid
            ORDER BY hr.creado_en DESC LIMIT 5
        """), {"uid": uid}).fetchall()
        print(f"  {nombre} (ID {uid}): rating={u[0]}, pj={u[1]}")
        for h in hr:
            print(f"    P{h[0]} ({h[1]}): {h[2]} + {h[3]} = {h[4]}")

    # 3. Listar TODOS los temp del torneo 38 y buscar migrables
    print(f"\n{'=' * 60}")
    print("3. TODOS LOS TEMP DEL TORNEO 38")
    print("=" * 60)
    
    temps = c.execute(text("""
        SELECT DISTINCT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido,
               u.rating, u.partidos_jugados
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
    
    print(f"  Total temp en torneo 38: {len(temps)}")
    migrables = []
    no_migrables = []
    for t in temps:
        reales = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido, u.rating
            FROM usuarios u
            JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.email NOT LIKE '%@driveplus.temp'
            AND LOWER(TRIM(p.nombre)) = LOWER(TRIM(:nom))
            AND LOWER(TRIM(p.apellido)) = LOWER(TRIM(:ape))
            AND u.id_usuario != :tid
        """), {"nom": t[3], "ape": t[4], "tid": t[0]}).fetchall()
        
        if reales:
            for r in reales:
                # Verificar si ya fue migrado (temp ya no está en parejas)
                en_parejas = c.execute(text("""
                    SELECT COUNT(*) FROM torneos_parejas 
                    WHERE torneo_id = 38 AND (jugador1_id = :tid OR jugador2_id = :tid)
                """), {"tid": t[0]}).fetchone()[0]
                if en_parejas > 0:
                    print(f"  🔄 MIGRABLE: {t[3]} {t[4]} TEMP={t[0]} (rating={t[5]}) -> REAL={r[0]} ({r[1]}, rating={r[5]})")
                    migrables.append((t[0], r[0], f"{t[3]} {t[4]}", t[5], r[5]))
                else:
                    print(f"  ✅ YA MIGRADO: {t[3]} {t[4]} TEMP={t[0]} -> REAL={r[0]}")
        else:
            no_migrables.append(t)
            print(f"  ❌ SIN CUENTA REAL: {t[3]} {t[4]} TEMP={t[0]} ({t[2]})")

    print(f"\n  Resumen: {len(migrables)} migrables, {len(no_migrables)} sin cuenta real")
    if migrables:
        print(f"\n  PENDIENTES DE MIGRAR:")
        for temp_id, real_id, nombre, t_rating, r_rating in migrables:
            print(f"    {nombre}: TEMP {temp_id} (rating {t_rating}) -> REAL {real_id} (rating {r_rating})")
