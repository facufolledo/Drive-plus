"""
Inscribir 2 parejas nuevas en torneo 38, categoría 6ta (ID 88):
- Pareja 11: Ruarte Leandro (ID 50) + Ellerak Benjamin (CREAR) - viernes desp de 15
- Pareja 12: Oliva Bautista (ID 200) + Cruz Juan (CREAR) - viernes desp 18, sábado desp 14
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
CATEGORIA_ID = 88

NUEVOS_JUGADORES = [
    {"nombre": "Benjamin", "apellido": "Ellerak", "username": "benjamin.ellerak", "email": "benjamin.ellerak@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Juan", "apellido": "Cruz", "username": "juan.cruz.t38", "email": "juan.cruz.t38@driveplus.temp", "sexo": "M", "rating": 1299},
]

# Restricciones = horarios en los que NO pueden jugar
PAREJAS = [
    # P11: Ruarte Leandro (50) + Ellerak Benjamin - viernes desp de 15 = restricción viernes antes de 15
    (50, "benjamin.ellerak",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"}]),

    # P12: Oliva Bautista (200) + Cruz Juan - viernes desp 18, sábado desp 14
    # Restricción: viernes antes de 18, sábado antes de 14
    (200, "juan.cruz.t38",
     [
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "14:00"},
     ]),
]


def inscribir():
    s = Session()
    try:
        print("=" * 60)
        print(f"INSCRIBIR 2 PAREJAS - TORNEO {TORNEO_ID} - 6ta (ID {CATEGORIA_ID})")
        print("=" * 60)

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
        for i, (j1, j2, restricciones) in enumerate(PAREJAS, 11):
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
        print(f"✅ LISTO - {total} parejas en 6ta del torneo {TORNEO_ID}")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
        s.rollback()
    finally:
        s.close()


if __name__ == "__main__":
    inscribir()
