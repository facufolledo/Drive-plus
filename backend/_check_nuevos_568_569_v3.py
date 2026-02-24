"""Revisar usuarios 568 y 569 - buscar temps y parejas"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Info usuarios
    print("=" * 60)
    print("USUARIOS 568 y 569")
    print("=" * 60)
    rows = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.id_categoria,
               p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.id_usuario IN (568, 569)
    """)).fetchall()
    for r in rows:
        print(f"  ID {r[0]}: user={r[1]}, email={r[2]}, rating={r[3]}, cat={r[4]}, perfil={r[5]} {r[6]}")

    # Buscar temps parecidos
    print("\n" + "=" * 60)
    print("TEMPS PARECIDOS")
    print("=" * 60)
    
    for uid in [568, 569]:
        perfil = conn.execute(text(
            "SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = :uid"
        ), {"uid": uid}).fetchone()
        
        if not perfil:
            print(f"\n  Usuario {uid}: Sin perfil")
            continue
        
        nombre, apellido = perfil[0], perfil[1] or ''
        print(f"\n  Usuario REAL {uid}: {nombre} {apellido}")
        
        temps = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.password_hash = 'temp_no_login'
              AND (
                LOWER(p.nombre) LIKE LOWER(:nombre) 
                OR LOWER(p.apellido) LIKE LOWER(:apellido)
              )
        """), {
            "nombre": f"%{nombre}%",
            "apellido": f"%{apellido}%" if apellido else "%ZZZZZ%",
        }).fetchall()
        
        for t in temps:
            print(f"    TEMP {t[0]}: user={t[1]}, rating={t[2]}, cat={t[3]}, perfil={t[4]} {t[5]}")
            
            # Parejas del temp
            parejas = conn.execute(text("""
                SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
                FROM torneos_parejas tp
                WHERE tp.jugador1_id = :tid OR tp.jugador2_id = :tid
            """), {"tid": t[0]}).fetchall()
            for pa in parejas:
                print(f"      Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")
            
            # Partidos donde aparece (via parejas)
            partidos = conn.execute(text("""
                SELECT pt.id_partido, pt.id_torneo, pt.fase, pt.estado, pt.pareja1_id, pt.pareja2_id
                FROM partidos pt
                WHERE pt.pareja1_id IN (SELECT id FROM torneos_parejas WHERE jugador1_id = :tid OR jugador2_id = :tid)
                   OR pt.pareja2_id IN (SELECT id FROM torneos_parejas WHERE jugador1_id = :tid OR jugador2_id = :tid)
                ORDER BY pt.id_partido
            """), {"tid": t[0]}).fetchall()
            print(f"      Partidos ({len(partidos)}):")
            for pp in partidos:
                print(f"        P{pp[0]}: T{pp[1]} fase={pp[2]} estado={pp[3]} pa1={pp[4]} pa2={pp[5]}")
        
        if not temps:
            print(f"    No se encontraron temps parecidos")
    
    # Parejas de los reales
    print("\n" + "=" * 60)
    print("PAREJAS DE LOS REALES")
    print("=" * 60)
    for uid in [568, 569]:
        parejas = conn.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
            FROM torneos_parejas tp
            WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
        """), {"uid": uid}).fetchall()
        if parejas:
            for pa in parejas:
                print(f"  Real {uid} -> Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")
        else:
            print(f"  Real {uid}: Sin parejas")
