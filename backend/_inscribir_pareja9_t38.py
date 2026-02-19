import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=engine)()

TORNEO_ID = 38
CATEGORIA_ID = 88  # 6ta

# Crear Samir Pablo
r = s.execute(text("""
    INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
    VALUES ('pablo.samir', 'pablo.samir@driveplus.temp', 'temp_no_login', 1299, 'M', 0)
    RETURNING id_usuario
"""))
samir_id = r.fetchone()[0]
s.execute(text("""
    INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
    VALUES (:uid, 'Pablo', 'Samir', 'Córdoba', 'Argentina')
"""), {"uid": samir_id})
print(f"✅ Pablo Samir (ID: {samir_id})")

# Crear Rodozaldovich Sebastián
r = s.execute(text("""
    INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
    VALUES ('sebastian.rodozaldovich', 'sebastian.rodozaldovich@driveplus.temp', 'temp_no_login', 1299, 'M', 0)
    RETURNING id_usuario
"""))
rodo_id = r.fetchone()[0]
s.execute(text("""
    INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
    VALUES (:uid, 'Sebastián', 'Rodozaldovich', 'Córdoba', 'Argentina')
"""), {"uid": rodo_id})
print(f"✅ Sebastián Rodozaldovich (ID: {rodo_id})")

s.commit()

# Restricciones: viernes antes de 18, sábado antes de 14
restricciones = json.dumps([
    {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"},
    {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "14:00"}
])

r = s.execute(text("""
    INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
    VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb))
    RETURNING id
"""), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": samir_id, "j2": rodo_id, "r": restricciones})
pid = r.fetchone()[0]
s.commit()

print(f"✅ Pareja 9 inscripta (ID: {pid}) - Samir/Rodozaldovich")

total = s.execute(text(
    "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]
print(f"Total parejas en 6ta: {total}")
s.close()
