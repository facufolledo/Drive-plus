"""Inscribir Magi Augusto + Gaspanello Juan en 4ta torneo 38
Viernes desp de las 18. Restricción: viernes 09-18
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

TORNEO_ID = 38
CATEGORIA_ID = 87

def get_or_create(username, email, nombre, apellido):
    r = s.execute(text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"), {"u": username}).fetchone()
    if r:
        print(f"  {nombre} {apellido} ya existe (ID: {r[0]})")
        return r[0]
    r = s.execute(text("""
        INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
        VALUES (:u, :e, 'temp_no_login', 1299, 'M', 0) RETURNING id_usuario
    """), {"u": username, "e": email})
    uid = r.fetchone()[0]
    s.execute(text("""
        INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
        VALUES (:uid, :n, :a, 'Córdoba', 'Argentina')
    """), {"uid": uid, "n": nombre, "a": apellido})
    print(f"  ✅ {nombre} {apellido} creado (ID: {uid})")
    return uid

try:
    j1 = get_or_create("augusto.magi", "augusto.magi@driveplus.temp", "Augusto", "Magi")
    j2 = get_or_create("juan.gaspanello", "juan.gaspanello@driveplus.temp", "Juan", "Gaspanello")
    s.commit()

    existe = s.execute(text("""
        SELECT id FROM torneos_parejas
        WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2)
            OR (jugador1_id = :j2 AND jugador2_id = :j1))
    """), {"t": TORNEO_ID, "j1": j1, "j2": j2}).fetchone()

    if existe:
        print(f"⚠️ Pareja ya existe (ID: {existe[0]})")
    else:
        restr = json.dumps([{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"}])
        r = s.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
            VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb)) RETURNING id
        """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": j1, "j2": j2, "r": restr})
        pid = r.fetchone()[0]
        s.commit()
        print(f"✅ Pareja {pid}: Magi Augusto (ID {j1}) + Gaspanello Juan (ID {j2})")

    total = s.execute(text(
        "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
    ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]
    print(f"\nTotal parejas en 4ta: {total}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback; traceback.print_exc()
    s.rollback()
finally:
    s.close()
