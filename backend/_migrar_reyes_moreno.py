"""Buscar cuentas reales de Emanuel Reyes y Aiken Moreno Nieto,
encontrar sus temps en T38, y migrar (reemplazar temp por real en parejas/partidos)."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # 1. Buscar temps
    print("=== TEMPS ===")
    for nombre, apellido in [("Emanuel", "Reyes"), ("Aiken", "Moreno")]:
        temps = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.password_hash, u.rating, u.id_categoria,
                   pu.nombre, pu.apellido
            FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE pu.nombre ILIKE :n AND pu.apellido ILIKE :a
        """), {"n": f"%{nombre}%", "a": f"%{apellido}%"}).fetchall()
        for t in temps:
            is_temp = t[2] == 'temp_no_login'
            print(f"  ID {t[0]}: {t[5]} {t[6]} user={t[1]} rating={t[3]} cat={t[4]} {'[TEMP]' if is_temp else '[REAL]'}")
    
    # 2. Buscar cuentas reales nuevas (password_hash vacío/null = Firebase)
    print("\n=== CUENTAS REALES RECIENTES (nombre parecido) ===")
    for search in ['reyes', 'moreno', 'aiken', 'emanuel']:
        reales = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.id_categoria,
                   pu.nombre, pu.apellido, u.password_hash
            FROM usuarios u LEFT JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE (pu.nombre ILIKE :s OR pu.apellido ILIKE :s OR u.nombre_usuario ILIKE :s)
            AND (u.password_hash IS NULL OR u.password_hash = '' OR u.password_hash != 'temp_no_login')
            ORDER BY u.id_usuario DESC
        """), {"s": f"%{search}%"}).fetchall()
        for r in reales:
            is_real = r[7] is None or r[7] == '' or r[7] != 'temp_no_login'
            print(f"  ID {r[0]}: {r[5]} {r[6]} user={r[1]} email={r[2]} rating={r[3]} cat={r[4]} {'[REAL]' if is_real else '[TEMP]'}")
    
    # 3. Buscar en parejas T38 dónde están los temps
    print("\n=== PAREJAS T38 CON ESTOS TEMPS ===")
    for tid in [516, 519]:  # Emanuel Reyes=516, Aiken Moreno=519
        parejas = c.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.categoria_id, tp.estado,
                   p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
            FROM torneos_parejas tp
            JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
            JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
            WHERE tp.torneo_id = 38 AND (tp.jugador1_id = :tid OR tp.jugador2_id = :tid)
        """), {"tid": tid}).fetchall()
        for p in parejas:
            print(f"  Pareja {p[0]}: {p[5]} / {p[6]} cat={p[3]} estado={p[4]} j1={p[1]} j2={p[2]}")
