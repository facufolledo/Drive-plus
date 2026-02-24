"""Migrar Joaquin Rivero: temp 513 -> real 576"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

TEMP_ID = 513
REAL_ID = 576

with engine.connect() as conn:
    temp = conn.execute(text("SELECT rating, id_categoria FROM usuarios WHERE id_usuario = :tid"), {"tid": TEMP_ID}).fetchone()
    print(f"Temp {TEMP_ID}: rating={temp[0]}, cat={temp[1]}")
    
    # 1. Copiar rating del temp al real
    conn.execute(text("UPDATE usuarios SET rating = :r, id_categoria = :c WHERE id_usuario = :rid"),
                {"r": temp[0], "c": temp[1], "rid": REAL_ID})
    
    # 2. Transferir parejas
    u1 = conn.execute(text("UPDATE torneos_parejas SET jugador1_id = :rid WHERE jugador1_id = :tid"), {"rid": REAL_ID, "tid": TEMP_ID}).rowcount
    u2 = conn.execute(text("UPDATE torneos_parejas SET jugador2_id = :rid WHERE jugador2_id = :tid"), {"rid": REAL_ID, "tid": TEMP_ID}).rowcount
    print(f"✅ Parejas transferidas: {u1 + u2}")
    
    # 3. Transferir historial rating
    conn.execute(text("""
        UPDATE historial_rating SET id_usuario = :rid WHERE id_usuario = :tid
        AND id_partido NOT IN (SELECT id_partido FROM historial_rating WHERE id_usuario = :rid2)
    """), {"rid": REAL_ID, "tid": TEMP_ID, "rid2": REAL_ID})
    conn.execute(text("DELETE FROM historial_rating WHERE id_usuario = :tid"), {"tid": TEMP_ID})
    
    # 4. Transferir circuito_puntos_jugador
    conn.execute(text("UPDATE circuito_puntos_jugador SET usuario_id = :rid WHERE usuario_id = :tid"), {"rid": REAL_ID, "tid": TEMP_ID})
    
    # 5. Recalcular partidos_jugados
    parejas = conn.execute(text("SELECT id FROM torneos_parejas WHERE jugador1_id = :uid OR jugador2_id = :uid"), {"uid": REAL_ID}).fetchall()
    pids = [p[0] for p in parejas]
    if pids:
        pids_str = ','.join(str(p) for p in pids)
        total = conn.execute(text(f"SELECT COUNT(*) FROM partidos WHERE estado = 'confirmado' AND (pareja1_id IN ({pids_str}) OR pareja2_id IN ({pids_str}))")).scalar()
        conn.execute(text("UPDATE usuarios SET partidos_jugados = :t WHERE id_usuario = :uid"), {"t": total, "uid": REAL_ID})
        print(f"✅ partidos_jugados = {total}")
    
    # 6. Borrar temp
    conn.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = :tid"), {"tid": TEMP_ID})
    conn.execute(text("DELETE FROM usuarios WHERE id_usuario = :tid AND password_hash = 'temp_no_login'"), {"tid": TEMP_ID})
    print(f"✅ Temp {TEMP_ID} borrado")
    
    conn.commit()
    
    # Verificar
    u = conn.execute(text("""
        SELECT u.rating, u.id_categoria, u.partidos_jugados, p.nombre, p.apellido
        FROM usuarios u LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.id_usuario = :uid
    """), {"uid": REAL_ID}).fetchone()
    print(f"\n✅ Real {REAL_ID}: {u[3]} {u[4]}, rating={u[0]}, cat={u[1]}, pj={u[2]}")
    
    exists = conn.execute(text("SELECT COUNT(*) FROM usuarios WHERE id_usuario = :tid"), {"tid": TEMP_ID}).scalar()
    print(f"Temp {TEMP_ID}: {'EXISTE ⚠️' if exists else 'BORRADO ✅'}")
