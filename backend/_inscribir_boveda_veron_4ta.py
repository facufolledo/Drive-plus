"""Inscribir Bóveda Marcos (temp) + Veron Martín (ID 24) en 4ta torneo 38
Horarios: viernes desp de las 18, resto libre
Restricción: viernes antes de 18
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
VERON_ID = 24

try:
    # 1. Crear Bóveda Marcos
    existe = s.execute(text(
        "SELECT id_usuario FROM usuarios WHERE nombre_usuario = 'marcos.boveda'"
    )).fetchone()

    if existe:
        boveda_id = existe[0]
        print(f"Bóveda Marcos ya existe (ID: {boveda_id})")
    else:
        r = s.execute(text("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
            VALUES ('marcos.boveda', 'marcos.boveda@driveplus.temp', 'temp_no_login', 1299, 'M', 0)
            RETURNING id_usuario
        """))
        boveda_id = r.fetchone()[0]
        s.execute(text("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
            VALUES (:uid, 'Marcos', 'Bóveda', 'Córdoba', 'Argentina')
        """), {"uid": boveda_id})
        s.commit()
        print(f"✅ Bóveda Marcos creado (ID: {boveda_id})")

    # 2. Inscribir pareja
    existe_p = s.execute(text("""
        SELECT id FROM torneos_parejas
        WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2)
            OR (jugador1_id = :j2 AND jugador2_id = :j1))
    """), {"t": TORNEO_ID, "j1": boveda_id, "j2": VERON_ID}).fetchone()

    if existe_p:
        print(f"⚠️ Pareja ya existe (ID: {existe_p[0]})")
    else:
        restricciones = json.dumps([
            {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"}
        ])
        r = s.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
            VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb))
            RETURNING id
        """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": boveda_id, "j2": VERON_ID, "r": restricciones})
        pid = r.fetchone()[0]
        s.commit()
        print(f"✅ Pareja {pid}: Bóveda Marcos (ID {boveda_id}) + Veron Martín (ID {VERON_ID})")

    # 3. Total parejas en 4ta
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
