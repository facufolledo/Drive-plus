"""Revisar usuarios 570-573, perfiles, y buscar temps para migrar"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

IDS = [570, 571, 572, 573]

with engine.connect() as conn:
    print("=" * 60)
    print("USUARIOS NUEVOS")
    print("=" * 60)
    rows = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.id_categoria,
               p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.id_usuario IN (570, 571, 572, 573)
        ORDER BY u.id_usuario
    """)).fetchall()
    for r in rows:
        print(f"  ID {r[0]}: user={r[1]}, email={r[2]}, rating={r[3]}, cat={r[4]}, perfil={r[5]} {r[6]}")

    print("\n" + "=" * 60)
    print("BUSCANDO TEMPS PARECIDOS")
    print("=" * 60)
    
    for uid in IDS:
        perfil = conn.execute(text(
            "SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = :uid"
        ), {"uid": uid}).fetchone()
        
        if not perfil or not perfil[0]:
            print(f"\n  Usuario {uid}: Sin perfil completo")
            continue
        
        nombre, apellido = perfil[0], perfil[1] or ''
        print(f"\n  REAL {uid}: {nombre} {apellido}")
        
        # Buscar por nombre Y apellido
        temps = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.password_hash = 'temp_no_login'
              AND (
                (LOWER(p.nombre) LIKE LOWER(:nombre) AND LOWER(p.apellido) LIKE LOWER(:apellido))
                OR LOWER(p.apellido) LIKE LOWER(:apellido)
              )
        """), {
            "nombre": f"%{nombre}%",
            "apellido": f"%{apellido}%" if apellido else "%ZZZZZ%",
        }).fetchall()
        
        if temps:
            for t in temps:
                print(f"    TEMP {t[0]}: user={t[1]}, rating={t[2]}, cat={t[3]}, perfil={t[4]} {t[5]}")
                
                parejas = conn.execute(text("""
                    SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id
                    FROM torneos_parejas tp
                    WHERE tp.jugador1_id = :tid OR tp.jugador2_id = :tid
                """), {"tid": t[0]}).fetchall()
                for pa in parejas:
                    print(f"      Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]}")
                
                partidos_count = conn.execute(text("""
                    SELECT COUNT(*) FROM partidos
                    WHERE pareja1_id IN (SELECT id FROM torneos_parejas WHERE jugador1_id = :tid OR jugador2_id = :tid)
                       OR pareja2_id IN (SELECT id FROM torneos_parejas WHERE jugador1_id = :tid OR jugador2_id = :tid)
                """), {"tid": t[0]}).scalar()
                print(f"      Partidos: {partidos_count}")
        else:
            print(f"    No se encontraron temps parecidos")
    
    # Parejas de los reales
    print("\n" + "=" * 60)
    print("PAREJAS DE LOS REALES")
    print("=" * 60)
    for uid in IDS:
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
