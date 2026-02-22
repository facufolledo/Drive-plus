"""Inscribir Ferreyra Pablo + Gudiño Carlos en 4ta torneo 38
Viernes: pueden de 14 a 16 o después de las 22
Restricción: viernes 16:00-22:00 (bloque donde NO pueden)
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
CATEGORIA_ID = 87  # 4ta

try:
    # Crear Ferreyra Pablo
    r = s.execute(text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = 'pablo.ferreyra'")).fetchone()
    if r:
        ferreyra_id = r[0]
        print(f"Ferreyra Pablo ya existe (ID: {ferreyra_id})")
    else:
        r = s.execute(text("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
            VALUES ('pablo.ferreyra', 'pablo.ferreyra@driveplus.temp', 'temp_no_login', 1299, 'M', 0)
            RETURNING id_usuario
        """))
        ferreyra_id = r.fetchone()[0]
        s.execute(text("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
            VALUES (:uid, 'Pablo', 'Ferreyra', 'Córdoba', 'Argentina')
        """), {"uid": ferreyra_id})
        print(f"✅ Ferreyra Pablo creado (ID: {ferreyra_id})")

    # Crear Gudiño Carlos
    r = s.execute(text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = 'carlos.gudino'")).fetchone()
    if r:
        gudino_id = r[0]
        print(f"Gudiño Carlos ya existe (ID: {gudino_id})")
    else:
        r = s.execute(text("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
            VALUES ('carlos.gudino', 'carlos.gudino@driveplus.temp', 'temp_no_login', 1299, 'M', 0)
            RETURNING id_usuario
        """))
        gudino_id = r.fetchone()[0]
        s.execute(text("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
            VALUES (:uid, 'Carlos', 'Gudiño', 'Córdoba', 'Argentina')
        """), {"uid": gudino_id})
        print(f"✅ Gudiño Carlos creado (ID: {gudino_id})")

    s.commit()

    # Inscribir pareja
    existe = s.execute(text("""
        SELECT id FROM torneos_parejas
        WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2)
            OR (jugador1_id = :j2 AND jugador2_id = :j1))
    """), {"t": TORNEO_ID, "j1": ferreyra_id, "j2": gudino_id}).fetchone()

    if existe:
        print(f"⚠️ Pareja ya existe (ID: {existe[0]})")
    else:
        restricciones = json.dumps([
            {"dias": ["viernes"], "horaInicio": "16:00", "horaFin": "22:00"}
        ])
        r = s.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
            VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb))
            RETURNING id
        """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": ferreyra_id, "j2": gudino_id, "r": restricciones})
        pid = r.fetchone()[0]
        s.commit()
        print(f"✅ Pareja {pid}: Ferreyra Pablo (ID {ferreyra_id}) + Gudiño Carlos (ID {gudino_id})")

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
