"""Check y migrar usuarios 575 y 576"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Info de los nuevos
    print("=== USUARIOS NUEVOS ===")
    for uid in [575, 576]:
        u = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.id_categoria, u.partidos_jugados,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        print(f"  ID {u[0]}: user={u[1]}, email={u[2]}, rating={u[3]}, cat={u[4]}, pj={u[5]}, perfil={u[6]} {u[7]}")

    # Buscar temps
    print("\n=== BUSCANDO TEMPS ===")
    for uid in [575, 576]:
        perfil = conn.execute(text("SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = :uid"), {"uid": uid}).fetchone()
        if not perfil or not perfil[0]:
            print(f"\n  {uid}: Sin perfil")
            continue
        nombre, apellido = perfil[0].strip(), (perfil[1] or '').strip()
        print(f"\n  REAL {uid}: {nombre} {apellido}")
        
        temps = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.rating, u.id_categoria, u.partidos_jugados,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.password_hash = 'temp_no_login'
              AND (LOWER(p.apellido) LIKE LOWER(:apellido) OR LOWER(p.nombre) LIKE LOWER(:nombre))
        """), {"apellido": f"%{apellido}%", "nombre": f"%{nombre}%"}).fetchall()
        
        for t in temps:
            print(f"    TEMP {t[0]}: {t[5]} {t[6]}, user={t[1]}, rating={t[2]}, cat={t[3]}, pj={t[4]}")
            parejas = conn.execute(text("""
                SELECT id, jugador1_id, jugador2_id, torneo_id
                FROM torneos_parejas WHERE jugador1_id = :tid OR jugador2_id = :tid
            """), {"tid": t[0]}).fetchall()
            for pa in parejas:
                print(f"      Pareja {pa[0]}: j1={pa[1]} j2={pa[2]} T{pa[3]}")
            
            pids = [pa[0] for pa in parejas]
            if pids:
                pids_str = ','.join(str(p) for p in pids)
                total = conn.execute(text(f"""
                    SELECT COUNT(*) FROM partidos WHERE estado = 'confirmado'
                      AND (pareja1_id IN ({pids_str}) OR pareja2_id IN ({pids_str}))
                """)).scalar()
                ganados = conn.execute(text(f"""
                    SELECT COUNT(*) FROM partidos WHERE estado = 'confirmado'
                      AND ganador_pareja_id IN ({pids_str})
                """)).scalar()
                print(f"      Partidos: {total} jugados, {ganados} ganados")
        
        if not temps:
            print(f"    No se encontraron temps")
