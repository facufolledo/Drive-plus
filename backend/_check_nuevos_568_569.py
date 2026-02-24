"""Revisar usuarios 568 y 569, sus perfiles, y buscar temps parecidos para migrar"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # 1. Info de usuarios 568 y 569
    print("=" * 60)
    print("USUARIOS 568 y 569")
    print("=" * 60)
    rows = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email, u.password_hash, u.rating, u.id_categoria,
               p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.id_usuario IN (568, 569)
    """)).fetchall()
    for r in rows:
        is_real = not r[3] or r[3] == '' or 'temp_no_login' not in (r[3] or '')
        print(f"  ID {r[0]}: user={r[1]}, email={r[2]}, real={'SI' if is_real else 'NO'}, rating={r[4]}, cat={r[5]}, perfil={r[6]} {r[7]}")

    # 2. Buscar temps con nombres parecidos
    print("\n" + "=" * 60)
    print("BUSCANDO TEMPS PARECIDOS")
    print("=" * 60)
    
    for uid in [568, 569]:
        perfil = conn.execute(text("""
            SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = :uid
        """), {"uid": uid}).fetchone()
        
        if not perfil or not perfil[0]:
            print(f"\n  Usuario {uid}: Sin perfil completo, no se puede buscar temps")
            continue
        
        nombre = perfil[0]
        apellido = perfil[1] or ''
        print(f"\n  Usuario {uid}: {nombre} {apellido}")
        
        # Buscar por nombre similar en temps
        temps = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.id_categoria,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.password_hash = 'temp_no_login'
              AND (
                LOWER(p.nombre) LIKE LOWER(:nombre) 
                OR LOWER(p.apellido) LIKE LOWER(:apellido)
                OR LOWER(u.nombre_usuario) LIKE LOWER(:nombre2)
                OR LOWER(u.nombre_usuario) LIKE LOWER(:apellido2)
              )
        """), {
            "nombre": f"%{nombre}%",
            "apellido": f"%{apellido}%" if apellido else "%ZZZZZ%",
            "nombre2": f"%{nombre}%",
            "apellido2": f"%{apellido}%" if apellido else "%ZZZZZ%",
        }).fetchall()
        
        if temps:
            for t in temps:
                print(f"    TEMP ID {t[0]}: user={t[1]}, email={t[2]}, rating={t[3]}, cat={t[4]}, perfil={t[5]} {t[6]}")
                
                # Ver si este temp tiene partidos
                partidos = conn.execute(text("""
                    SELECT COUNT(*) FROM partidos p
                    JOIN torneos_parejas tp ON (tp.id = p.pareja1_id OR tp.id = p.pareja2_id)
                    WHERE tp.jugador1_id = :tid OR tp.jugador2_id = :tid
                """), {"tid": t[0]}).scalar()
                print(f"      Partidos: {partidos}")
                
                # Ver parejas del temp
                parejas = conn.execute(text("""
                    SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tc.torneo_id, tc.categoria_id
                    FROM torneos_parejas tp
                    JOIN torneo_categorias tc ON tc.id = tp.torneo_categoria_id
                    WHERE tp.jugador1_id = :tid OR tp.jugador2_id = :tid
                """), {"tid": t[0]}).fetchall()
                for pa in parejas:
                    print(f"      Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]} cat={pa[4]}")
        else:
            print(f"    No se encontraron temps parecidos")
    
    # 3. Ver si los usuarios 568/569 ya tienen parejas
    print("\n" + "=" * 60)
    print("PAREJAS ACTUALES DE 568 y 569")
    print("=" * 60)
    for uid in [568, 569]:
        parejas = conn.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tc.torneo_id, tc.categoria_id
            FROM torneos_parejas tp
            JOIN torneo_categorias tc ON tc.id = tp.torneo_categoria_id
            WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
        """), {"uid": uid}).fetchall()
        if parejas:
            for pa in parejas:
                print(f"  Usuario {uid} -> Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} torneo={pa[3]} cat={pa[4]}")
        else:
            print(f"  Usuario {uid}: Sin parejas")
