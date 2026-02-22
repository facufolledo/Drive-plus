"""Inscribir Ocampo + Romero en 4ta torneo 38"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 38
CATEGORIA_ID = 87

NUEVOS = [
    {"nombre": "NN", "apellido": "Ocampo", "username": "nn.ocampo.t38", "email": "nn.ocampo.t38@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "NN", "apellido": "Romero", "username": "nn.romero.t38", "email": "nn.romero.t38@driveplus.temp", "sexo": "M", "rating": 1299},
]

def run():
    s = Session()
    try:
        ids = {}
        for j in NUEVOS:
            existe = s.execute(text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"), {"u": j["username"]}).fetchone()
            if existe:
                ids[j["username"]] = existe[0]
                print(f"⚠️  {j['apellido']} ya existe (ID: {existe[0]})")
                continue
            r = s.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
                VALUES (:u, :e, 'temp_no_login', :rat, :sex, 0) RETURNING id_usuario
            """), {"u": j["username"], "e": j["email"], "rat": j["rating"], "sex": j["sexo"]})
            uid = r.fetchone()[0]
            ids[j["username"]] = uid
            s.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:uid, :nom, :ape, 'Córdoba', 'Argentina')
            """), {"uid": uid, "nom": j["nombre"], "ape": j["apellido"]})
            print(f"✅ {j['nombre']} {j['apellido']} creado (ID: {uid})")
        s.commit()

        j1 = ids["nn.ocampo.t38"]
        j2 = ids["nn.romero.t38"]
        restr = json.dumps([
            {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
            {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "10:00"},
        ])
        r = s.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
            VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb)) RETURNING id
        """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": j1, "j2": j2, "r": restr})
        pid = r.fetchone()[0]
        s.commit()
        print(f"✅ Pareja inscrita (ID: {pid}) - Ocampo/Romero - viernes ≥15, sábado ≥10")

        total = s.execute(text(
            "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
        ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]
        print(f"Total parejas en 4ta: {total}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
        s.rollback()
    finally:
        s.close()

if __name__ == "__main__":
    run()
