"""
Diagnóstico completo:
1. Lucas Apostolo (574) - buscar temp y migrar
2. Benjamin Hrellac (568/502) - verificar estado, arreglar partidos_jugados/wins
3. Migraciones anteriores (Juan Magi 562/511, Flavio Palacio 564/542) - verificar
4. Listar todos los temps ya migrados para borrar
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Columnas de usuarios relevantes
    cols = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'usuarios' ORDER BY ordinal_position
    """)).fetchall()
    print("Columnas usuarios:", [c[0] for c in cols])

    # ============ 1. LUCAS APOSTOLO ============
    print("\n" + "=" * 60)
    print("1. LUCAS APOSTOLO (574)")
    print("=" * 60)
    
    real574 = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria, u.partidos_jugados, u.partidos_ganados,
               p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.id_usuario = 574
    """)).fetchone()
    print(f"  Real 574: {real574[6]} {real574[7]}, rating={real574[2]}, cat={real574[3]}, pj={real574[4]}, pg={real574[5]}")
    
    # Buscar temp
    temps574 = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria, u.partidos_jugados, u.partidos_ganados,
               p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.password_hash = 'temp_no_login'
          AND (LOWER(p.apellido) LIKE '%apostolo%' OR LOWER(p.nombre) LIKE '%lucas%apostolo%'
               OR LOWER(u.nombre_usuario) LIKE '%apostolo%')
    """)).fetchall()
    for t in temps574:
        print(f"  TEMP {t[0]}: {t[6]} {t[7]}, user={t[1]}, rating={t[2]}, cat={t[3]}, pj={t[4]}, pg={t[5]}")
        # Parejas
        parejas = conn.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
            FROM torneos_parejas tp WHERE tp.jugador1_id = :tid OR tp.jugador2_id = :tid
        """), {"tid": t[0]}).fetchall()
        for pa in parejas:
            print(f"    Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")
        # Partidos
        partidos = conn.execute(text("""
            SELECT pt.id_partido, pt.fase, pt.estado, pt.pareja1_id, pt.pareja2_id, pt.ganador_pareja_id
            FROM partidos pt
            WHERE pt.pareja1_id IN (SELECT id FROM torneos_parejas WHERE jugador1_id = :tid OR jugador2_id = :tid)
               OR pt.pareja2_id IN (SELECT id FROM torneos_parejas WHERE jugador1_id = :tid OR jugador2_id = :tid)
            ORDER BY pt.id_partido
        """), {"tid": t[0]}).fetchall()
        print(f"    Partidos ({len(partidos)}):")
        for pp in partidos:
            print(f"      P{pp[0]}: {pp[1]} {pp[2]} pa1={pp[3]} pa2={pp[4]} ganador={pp[5]}")

    # ============ 2. BENJAMIN HRELLAC ============
    print("\n" + "=" * 60)
    print("2. BENJAMIN HRELLAC (real=568, temp=502)")
    print("=" * 60)
    
    for uid in [568, 502]:
        u = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria, u.partidos_jugados, u.partidos_ganados,
                   u.password_hash, p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        is_temp = u[6] == 'temp_no_login'
        print(f"  {'TEMP' if is_temp else 'REAL'} {uid}: {u[7]} {u[8]}, rating={u[2]}, cat={u[3]}, pj={u[4]}, pg={u[5]}")
        
        parejas = conn.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
            FROM torneos_parejas tp WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
        """), {"uid": uid}).fetchall()
        for pa in parejas:
            print(f"    Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")

    # ============ 3. MIGRACIONES ANTERIORES ============
    print("\n" + "=" * 60)
    print("3. MIGRACIONES ANTERIORES")
    print("=" * 60)
    
    # Juan Magi 562/511, Flavio Palacio 564/542
    for real_id, temp_id, nombre in [(562, 511, "Juan Magi"), (564, 542, "Flavio Palacio")]:
        for uid in [real_id, temp_id]:
            u = conn.execute(text("""
                SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria, u.partidos_jugados, u.partidos_ganados,
                       u.password_hash, p.nombre, p.apellido
                FROM usuarios u
                LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
                WHERE u.id_usuario = :uid
            """), {"uid": uid}).fetchone()
            if u:
                is_temp = u[6] == 'temp_no_login'
                print(f"  {nombre} {'TEMP' if is_temp else 'REAL'} {uid}: rating={u[2]}, cat={u[3]}, pj={u[4]}, pg={u[5]}")
                parejas = conn.execute(text("""
                    SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
                    FROM torneos_parejas tp WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
                """), {"uid": uid}).fetchall()
                for pa in parejas:
                    print(f"    Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")
            else:
                print(f"  {nombre} {uid}: NO EXISTE")
