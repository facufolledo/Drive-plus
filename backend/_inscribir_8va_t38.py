"""Inscribir 9 parejas en 8va (cat 89) torneo 38 (ya hay 1: Ocaña/Millicay J = 647)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 38
CATEGORIA_ID = 89  # 8va

# Jugadores nuevos (temp)
NUEVOS = [
    {"nombre": "Gustavo", "apellido": "Moreno", "username": "gustavo.moreno.8va", "email": "gustavo.moreno.8va@driveplus.temp"},
    {"nombre": "Miguel", "apellido": "Antúnez", "username": "miguel.antunez", "email": "miguel.antunez@driveplus.temp"},
    {"nombre": "Álvaro", "apellido": "Ferreyra", "username": "alvaro.ferreyra", "email": "alvaro.ferreyra@driveplus.temp"},
    {"nombre": "Agustín", "apellido": "Cortez", "username": "agustin.cortez", "email": "agustin.cortez@driveplus.temp"},
    {"nombre": "Lucas", "apellido": "Mercado Luna", "username": "lucas.mercadoluna", "email": "lucas.mercadoluna@driveplus.temp"},
    {"nombre": "Facundo", "apellido": "Callazo", "username": "facundo.callazo", "email": "facundo.callazo@driveplus.temp"},
    {"nombre": "Maxi", "apellido": "Frías", "username": "maxi.frias", "email": "maxi.frias@driveplus.temp"},
    {"nombre": "Daniel", "apellido": "Pérez", "username": "daniel.perez.8va", "email": "daniel.perez.8va@driveplus.temp"},
    {"nombre": "Santiago", "apellido": "Rodríguez", "username": "santiago.rodriguez.8va", "email": "santiago.rodriguez.8va@driveplus.temp"},
    {"nombre": "Matías", "apellido": "Castelli", "username": "matias.castelli", "email": "matias.castelli@driveplus.temp"},
    {"nombre": "Maximiliano", "apellido": "Pérez", "username": "maximiliano.perez", "email": "maximiliano.perez@driveplus.temp"},
    {"nombre": "Facundo", "apellido": "Rodríguez", "username": "facundo.rodriguez.8va", "email": "facundo.rodriguez.8va@driveplus.temp"},
    {"nombre": "Flavio", "apellido": "Palacio", "username": "flavio.palacio", "email": "flavio.palacio@driveplus.temp"},
    {"nombre": "Ramiro", "apellido": "Porras", "username": "ramiro.porras", "email": "ramiro.porras@driveplus.temp"},
    {"nombre": "Mateo", "apellido": "Algarrilla", "username": "mateo.algarrilla", "email": "mateo.algarrilla@driveplus.temp"},
    {"nombre": "Hugo", "apellido": "Palma", "username": "hugo.palma", "email": "hugo.palma@driveplus.temp"},
    {"nombre": "Sergio", "apellido": "Tapia", "username": "sergio.tapia", "email": "sergio.tapia@driveplus.temp"},
]

# Parejas: (j1, j2, restricciones)
# j1/j2 = username (temp) o int (ID existente)
PAREJAS = [
    # P1: Moreno Gustavo + Antúnez Miguel - vie desp 22
    ("gustavo.moreno.8va", "miguel.antunez",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"}]),

    # P3: Ferreyra Álvaro + Cortez Agustín - vie desp 21
    ("alvaro.ferreyra", "agustin.cortez",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}]),

    # P4: Mercado Luna Lucas + Callazo Facundo - desp 18
    ("lucas.mercadoluna", "facundo.callazo",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"}]),

    # P5: Frías Maxi + Pérez Daniel - solo sábado
    ("maxi.frias", "daniel.perez.8va",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "23:30"}]),

    # P6: Rodríguez Santiago + Castelli Matías - vie 15-17 y desp 20, sáb desp 12
    ("santiago.rodriguez.8va", "matias.castelli",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
      {"dias": ["viernes"], "horaInicio": "17:00", "horaFin": "20:00"},
      {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"}]),

    # P7: Pérez Maximiliano + Rodríguez Facundo - vie 14-18 y desp 22
    ("maximiliano.perez", "facundo.rodriguez.8va",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "14:00"},
      {"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "22:00"}]),

    # P8: Palacio Flavio + Porras Ramiro - vie 15-17 y desp 22
    ("flavio.palacio", "ramiro.porras",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
      {"dias": ["viernes"], "horaInicio": "17:00", "horaFin": "22:00"}]),

    # P9: Algarrilla Mateo + Millicay Gustavo (ID 5) - vie no puede
    ("mateo.algarrilla", 5,
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "23:30"}]),

    # P10: Palma Hugo + Tapia Sergio - vie no puede
    ("hugo.palma", "sergio.tapia",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "23:30"}]),
]


def inscribir():
    s = Session()
    try:
        print("=" * 60)
        print(f"INSCRIBIR 9 PAREJAS - TORNEO {TORNEO_ID} - 8va (ID {CATEGORIA_ID})")
        print("=" * 60)

        existing = s.execute(text(
            "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
        ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]
        print(f"\nParejas existentes en 8va: {existing}")

        # 1. Crear jugadores nuevos
        nuevos_ids = {}
        print("\n📝 Creando jugadores nuevos...")
        for j in NUEVOS:
            existe = s.execute(text(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
            ), {"u": j["username"]}).fetchone()
            if existe:
                nuevos_ids[j["username"]] = existe[0]
                print(f"   ⚠️  {j['nombre']} {j['apellido']} ya existe (ID: {existe[0]})")
                continue
            r = s.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
                VALUES (:u, :e, 'temp_no_login', 1299, 'M', 0) RETURNING id_usuario
            """), {"u": j["username"], "e": j["email"]})
            uid = r.fetchone()[0]
            nuevos_ids[j["username"]] = uid
            s.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:uid, :nom, :ape, 'Córdoba', 'Argentina')
            """), {"uid": uid, "nom": j["nombre"], "ape": j["apellido"]})
            print(f"   ✅ {j['nombre']} {j['apellido']} creado (ID: {uid})")
        s.commit()

        # 2. Inscribir parejas
        print(f"\n👥 Inscribiendo parejas...")
        for i, (j1, j2, restricciones) in enumerate(PAREJAS, 1):
            j1_id = j1 if isinstance(j1, int) else nuevos_ids[j1]
            j2_id = j2 if isinstance(j2, int) else nuevos_ids[j2]

            existe = s.execute(text("""
                SELECT id FROM torneos_parejas
                WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2)
                    OR (jugador1_id = :j2 AND jugador2_id = :j1))
            """), {"t": TORNEO_ID, "j1": j1_id, "j2": j2_id}).fetchone()
            if existe:
                print(f"   ⚠️  Pareja {i} ya existe (ID: {existe[0]})")
                continue

            restr_json = json.dumps(restricciones)
            r = s.execute(text("""
                INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
                VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb)) RETURNING id
            """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": j1_id, "j2": j2_id, "r": restr_json})
            pid = r.fetchone()[0]
            print(f"   ✅ Pareja {i} (ID: {pid}) - {j1_id}/{j2_id}")
        s.commit()

        total = s.execute(text(
            "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
        ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]
        print(f"\n{'=' * 60}")
        print(f"✅ LISTO - {total} parejas en 8va del torneo {TORNEO_ID}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
        s.rollback()
    finally:
        s.close()

if __name__ == "__main__":
    inscribir()
