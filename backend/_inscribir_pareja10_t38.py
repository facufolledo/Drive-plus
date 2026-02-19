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

# Buscar Ligorria Lisandro
r = s.execute(text("""
    SELECT u.id_usuario, u.nombre_usuario, p.nombre, p.apellido
    FROM usuarios u LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
    WHERE LOWER(p.apellido) LIKE '%ligorria%' OR LOWER(u.nombre_usuario) LIKE '%ligorria%'
""")).fetchall()
for row in r:
    print(f"  Ligorria: ID:{row[0]} user:{row[1]} nombre:{row[2]} {row[3]}")

if not r:
    print("❌ Ligorria no encontrado")
    sys.exit()

ligorria_id = r[0][0]

# Crear Díaz Mateo (no está en la app)
r = s.execute(text("""
    INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
    VALUES ('mateo.diaz.t38', 'mateo.diaz.t38@driveplus.temp', 'temp_no_login', 1299, 'M', 0)
    RETURNING id_usuario
"""))
diaz_id = r.fetchone()[0]
s.execute(text("""
    INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
    VALUES (:uid, 'Mateo', 'Díaz', 'Córdoba', 'Argentina')
"""), {"uid": diaz_id})
print(f"✅ Mateo Díaz creado (ID: {diaz_id})")
s.commit()

# Restricción: viernes antes de 19
restricciones = json.dumps([
    {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
])

r = s.execute(text("""
    INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
    VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb))
    RETURNING id
"""), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": ligorria_id, "j2": diaz_id, "r": restricciones})
pid = r.fetchone()[0]
s.commit()

print(f"✅ Pareja 10 inscripta (ID: {pid}) - Ligorria {ligorria_id} / Díaz {diaz_id}")

total = s.execute(text(
    "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]
print(f"Total parejas en 6ta: {total}")
s.close()
