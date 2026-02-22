"""
Inscribir 9 parejas en torneo 38, categoría 4ta (ID 87):
P1: Quipildor Nahuel + Brizuela Amado - viernes desp 22, sábado desp 17
P2: Olivera Matías + Gurgone Kevin - viernes desp 19
P3: Magi Juan + Mercado Joaquín - viernes desp 21
P4: Nieto Axel (ID 75) + Calderón Juan (ID 201) - viernes a las 18 sí o sí, sábado desp 11
P5: Rivero Joaquín + Centeno Alejo - viernes desp 15, sábado desp 10
P6: Loto Juan + Reyes Emanuel - viernes desp 18, sábado desp 17
P7: Vallejos Ariel + Toledo Emanuel - viernes 18-21, sábado desp 18
P8: Moreno Aiken + Nieto Camilo (ID 504) - viernes desp 19
P9: Ligorria Lisandro (ID 52) + Brizuela Agustín - viernes desp 20
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 38
CATEGORIA_ID = 87  # 4ta masculino

NUEVOS_JUGADORES = [
    {"nombre": "Nahuel", "apellido": "Quipildor", "username": "nahuel.quipildor", "email": "nahuel.quipildor@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Amado", "apellido": "Brizuela", "username": "amado.brizuela", "email": "amado.brizuela@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Matías", "apellido": "Olivera", "username": "matias.olivera.t38", "email": "matias.olivera.t38@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Kevin", "apellido": "Gurgone", "username": "kevin.gurgone", "email": "kevin.gurgone@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Juan", "apellido": "Magi", "username": "juan.magi", "email": "juan.magi@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Joaquín", "apellido": "Mercado", "username": "joaquin.mercado.t38", "email": "joaquin.mercado.t38@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Joaquín", "apellido": "Rivero", "username": "joaquin.rivero", "email": "joaquin.rivero@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Alejo", "apellido": "Centeno", "username": "alejo.centeno", "email": "alejo.centeno@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Juan", "apellido": "Loto", "username": "juan.loto", "email": "juan.loto@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Emanuel", "apellido": "Reyes", "username": "emanuel.reyes", "email": "emanuel.reyes@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Ariel", "apellido": "Vallejos", "username": "ariel.vallejos", "email": "ariel.vallejos@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Emanuel", "apellido": "Toledo", "username": "emanuel.toledo", "email": "emanuel.toledo@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Aiken", "apellido": "Moreno", "username": "aiken.moreno", "email": "aiken.moreno@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Agustín", "apellido": "Brizuela", "username": "agustin.brizuela", "email": "agustin.brizuela@driveplus.temp", "sexo": "M", "rating": 1299},
]

# Restricciones = horarios en los que NO pueden jugar
PAREJAS = [
    # P1: Quipildor Nahuel + Brizuela Amado - viernes desp 22, sábado desp 17
    # Restricción: viernes antes de 22, sábado antes de 17
    ("nahuel.quipildor", "amado.brizuela",
     [
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "17:00"},
     ]),

    # P2: Olivera Matías + Gurgone Kevin - viernes desp 19
    # Restricción: viernes antes de 19
    ("matias.olivera.t38", "kevin.gurgone",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}]),

    # P3: Magi Juan + Mercado Joaquín - viernes desp 21
    # Restricción: viernes antes de 21
    ("juan.magi", "joaquin.mercado.t38",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}]),

    # P4: Nieto Axel (75) + Calderón Juan (201) - viernes a las 18 sí o sí, sábado desp 11
    # Restricción: viernes antes de 18 y después de 19:10 (solo 18hs), sábado antes de 11
    (75, 201,
     [
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"},
         {"dias": ["viernes"], "horaInicio": "19:10", "horaFin": "23:30"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "11:00"},
     ]),

    # P5: Rivero Joaquín + Centeno Alejo - viernes desp 15, sábado desp 10
    # Restricción: viernes antes de 15, sábado antes de 10
    ("joaquin.rivero", "alejo.centeno",
     [
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "10:00"},
     ]),

    # P6: Loto Juan + Reyes Emanuel - viernes desp 18, sábado desp 17
    # Restricción: viernes antes de 18, sábado antes de 17
    ("juan.loto", "emanuel.reyes",
     [
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "17:00"},
     ]),

    # P7: Vallejos Ariel + Toledo Emanuel - viernes 18-21, sábado desp 18
    # Restricción: viernes antes de 18 y después de 21, sábado antes de 18
    ("ariel.vallejos", "emanuel.toledo",
     [
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"},
         {"dias": ["viernes"], "horaInicio": "21:00", "horaFin": "23:30"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "18:00"},
     ]),

    # P8: Moreno Aiken + Nieto Camilo (504) - viernes desp 19
    # Restricción: viernes antes de 19
    ("aiken.moreno", 504,
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}]),

    # P9: Ligorria Lisandro (52) + Brizuela Agustín - viernes desp 20
    # Restricción: viernes antes de 20
    (52, "agustin.brizuela",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}]),
]


def inscribir():
    s = Session()
    try:
        print("=" * 60)
        print(f"INSCRIBIR 9 PAREJAS - TORNEO {TORNEO_ID} - 4ta (ID {CATEGORIA_ID})")
        print("=" * 60)

        # Verificar parejas existentes en 4ta
        existing = s.execute(text(
            "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
        ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]
        print(f"\n  Parejas existentes en 4ta: {existing}")

        # 1. Crear jugadores nuevos
        nuevos_ids = {}
        print("\n📝 Creando jugadores nuevos...")
        for j in NUEVOS_JUGADORES:
            existe = s.execute(text(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
            ), {"u": j["username"]}).fetchone()

            if existe:
                nuevos_ids[j["username"]] = existe[0]
                print(f"   ⚠️  {j['nombre']} {j['apellido']} ya existe (ID: {existe[0]})")
                continue

            r = s.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
                VALUES (:u, :e, 'temp_no_login', :rat, :sex, 0)
                RETURNING id_usuario
            """), {"u": j["username"], "e": j["email"], "rat": j["rating"], "sex": j["sexo"]})
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
                VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb))
                RETURNING id
            """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": j1_id, "j2": j2_id, "r": restr_json})
            pid = r.fetchone()[0]
            print(f"   ✅ Pareja {i} (ID: {pid}) - {j1_id}/{j2_id} - {len(restricciones)} restricción(es)")

        s.commit()

        # 3. Resumen
        total = s.execute(text(
            "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
        ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]

        print(f"\n{'=' * 60}")
        print(f"✅ LISTO - {total} parejas en 4ta del torneo {TORNEO_ID}")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
        s.rollback()
    finally:
        s.close()


if __name__ == "__main__":
    inscribir()
