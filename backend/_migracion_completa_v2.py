"""Diagnóstico completo de migraciones"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

def info_usuario(conn, uid):
    u = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria, u.partidos_jugados,
               u.password_hash, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.id_usuario = :uid
    """), {"uid": uid}).fetchone()
    if not u:
        return None
    is_temp = u[5] == 'temp_no_login'
    return {
        "id": u[0], "user": u[1], "rating": u[2], "cat": u[3], "pj": u[4],
        "is_temp": is_temp, "nombre": u[6], "apellido": u[7]
    }

def parejas_usuario(conn, uid):
    return conn.execute(text("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
        FROM torneos_parejas tp WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
    """), {"uid": uid}).fetchall()

def partidos_usuario(conn, uid):
    """Contar partidos reales (confirmados) donde el usuario participó"""
    return conn.execute(text("""
        SELECT pt.id_partido, pt.fase, pt.estado, pt.pareja1_id, pt.pareja2_id, pt.ganador_pareja_id
        FROM partidos pt
        WHERE pt.estado = 'confirmado'
          AND (pt.pareja1_id IN (SELECT id FROM torneos_parejas WHERE jugador1_id = :uid OR jugador2_id = :uid)
               OR pt.pareja2_id IN (SELECT id FROM torneos_parejas WHERE jugador1_id = :uid OR jugador2_id = :uid))
        ORDER BY pt.id_partido
    """), {"uid": uid}).fetchall()

with engine.connect() as conn:
    # ============ 1. LUCAS APOSTOLO (574) ============
    print("=" * 60)
    print("1. LUCAS APOSTOLO (574)")
    print("=" * 60)
    
    r574 = info_usuario(conn, 574)
    print(f"  Real 574: {r574['nombre']} {r574['apellido']}, rating={r574['rating']}, cat={r574['cat']}, pj={r574['pj']}")
    
    temps = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria, u.partidos_jugados,
               p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.password_hash = 'temp_no_login'
          AND (LOWER(p.apellido) LIKE '%apostolo%' OR LOWER(u.nombre_usuario) LIKE '%apostolo%')
    """)).fetchall()
    for t in temps:
        print(f"  TEMP {t[0]}: {t[5]} {t[6]}, user={t[1]}, rating={t[2]}, cat={t[3]}, pj={t[4]}")
        for pa in parejas_usuario(conn, t[0]):
            print(f"    Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")
        pts = partidos_usuario(conn, t[0])
        ganados = sum(1 for p in pts if 
            (p[3] in [pa[0] for pa in parejas_usuario(conn, t[0])] and p[5] == p[3]) or
            (p[4] in [pa[0] for pa in parejas_usuario(conn, t[0])] and p[5] == p[4]))
        print(f"    Partidos confirmados: {len(pts)}, ganados: {ganados}")

    # ============ 2. BENJAMIN HRELLAC (568/502) ============
    print("\n" + "=" * 60)
    print("2. BENJAMIN HRELLAC (real=568, temp=502)")
    print("=" * 60)
    
    for uid in [568, 502]:
        u = info_usuario(conn, uid)
        label = "TEMP" if u['is_temp'] else "REAL"
        print(f"  {label} {uid}: {u['nombre']} {u['apellido']}, rating={u['rating']}, cat={u['cat']}, pj={u['pj']}")
        for pa in parejas_usuario(conn, uid):
            print(f"    Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")
        pts = partidos_usuario(conn, uid)
        pareja_ids = [pa[0] for pa in parejas_usuario(conn, uid)]
        ganados = sum(1 for p in pts if p[5] in pareja_ids)
        print(f"    Partidos confirmados: {len(pts)}, ganados: {ganados}")

    # ============ 3. MIGRACIONES ANTERIORES ============
    print("\n" + "=" * 60)
    print("3. MIGRACIONES ANTERIORES (Juan Magi 562/511, Flavio Palacio 564/542)")
    print("=" * 60)
    
    for real_id, temp_id, nombre in [(562, 511, "Juan Magi"), (564, 542, "Flavio Palacio")]:
        for uid in [real_id, temp_id]:
            u = info_usuario(conn, uid)
            if u:
                label = "TEMP" if u['is_temp'] else "REAL"
                print(f"  {nombre} {label} {uid}: rating={u['rating']}, cat={u['cat']}, pj={u['pj']}")
                for pa in parejas_usuario(conn, uid):
                    print(f"    Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")
                pts = partidos_usuario(conn, uid)
                pareja_ids = [pa[0] for pa in parejas_usuario(conn, uid)]
                ganados = sum(1 for p in pts if p[5] in pareja_ids)
                print(f"    Partidos confirmados: {len(pts)}, ganados: {ganados}")
