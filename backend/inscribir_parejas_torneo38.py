#!/usr/bin/env python3
"""
Inscribir 8 parejas en categoría 6ta del torneo 38.
Crea usuarios nuevos en BD para los que no están en la app.
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
CATEGORIA_ID = 88  # 6ta masculino

# Jugadores que NO están en la app (hay que crearlos)
NUEVOS_JUGADORES = [
    {"nombre": "Mateo", "apellido": "Algarrilla", "username": "mateo.algarrilla", "email": "mateo.algarrilla@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Maxi", "apellido": "Vega", "username": "maxi.vega", "email": "maxi.vega@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Mario", "apellido": "Santander", "username": "mario.santander", "email": "mario.santander@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Ramiro", "apellido": "Ortiz", "username": "ramiro.ortiz.t38", "email": "ramiro.ortiz.t38@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Álvaro", "apellido": "Díaz", "username": "alvaro.diaz.t38", "email": "alvaro.diaz.t38@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Joaquín", "apellido": "Brizuela", "username": "joaquin.brizuela", "email": "joaquin.brizuela@driveplus.temp", "sexo": "M", "rating": 1299},
    {"nombre": "Eduardo", "apellido": "Tasiukaz", "username": "eduardo.tasiukaz", "email": "eduardo.tasiukaz@driveplus.temp", "sexo": "M", "rating": 1299},
]

# Parejas: (jugador1, jugador2, restricciones)
# jugador = ID existente (int) o username nuevo (str)
# Restricciones = horarios en los que NO pueden jugar
PAREJAS = [
    # P1: Algarrilla Mateo / Montivero Federico - viernes antes de 18
    ("mateo.algarrilla", 43,
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"}]),

    # P2: Millicay Gustavo / Vera Jeremías - viernes antes de 19
    (5, 228,
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}]),

    # P3: Giordano Matías / Tapia Damián - solo pueden 16:00-17:30 y 23:00-23:30
    # Restricción: no pueden de 09-16, ni de 17:30-23, ni de 23:30-24
    (136, 217,
     [
         {"dias": ["viernes", "sabado", "domingo"], "horaInicio": "09:00", "horaFin": "16:00"},
         {"dias": ["viernes", "sabado", "domingo"], "horaInicio": "17:30", "horaFin": "23:00"},
     ]),

    # P4: Farran Bastian / Vega Maxi - viernes 14-17, resto libre
    # Restricción: viernes antes de 14 y después de 17
    (240, "maxi.vega",
     [
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "14:00"},
         {"dias": ["viernes"], "horaInicio": "17:00", "horaFin": "23:00"},
     ]),

    # P5: Lobos Javier / Santander Mario - viernes 19-22, resto libre
    # Restricción: viernes antes de 19 y después de 22
    (41, "mario.santander",
     [
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"},
         {"dias": ["viernes"], "horaInicio": "22:00", "horaFin": "23:00"},
     ]),

    # P6: Ortiz Ramiro / Speziale Tomás - viernes desp de 16, resto libre
    # Restricción: viernes antes de 16
    ("ramiro.ortiz.t38", 197,
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "16:00"}]),

    # P7: Díaz Álvaro / Brizuela Joaquín - viernes desp de 19, resto libre
    # Restricción: viernes antes de 19
    ("alvaro.diaz.t38", "joaquin.brizuela",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}]),

    # P8: Alegre Franco / Tasiukaz Eduardo - viernes desp de 20, resto libre
    # Restricción: viernes antes de 20
    (490, "eduardo.tasiukaz",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}]),
]


def inscribir():
    s = Session()
    try:
        print("=" * 70)
        print(f"INSCRIBIR PAREJAS - TORNEO {TORNEO_ID} - CATEGORÍA 6ta (ID {CATEGORIA_ID})")
        print("=" * 70)

        # 1. Crear jugadores nuevos
        nuevos_ids = {}
        print("\n📝 Creando jugadores nuevos...")
        for j in NUEVOS_JUGADORES:
            # Verificar si ya existe
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

            print(f"   ✅ {j['nombre']} {j['apellido']} (ID: {uid})")

        s.commit()
        print(f"   💾 {len(nuevos_ids)} jugadores listos")

        # 2. Inscribir parejas
        print(f"\n👥 Inscribiendo parejas...")
        for i, (j1, j2, restricciones) in enumerate(PAREJAS, 1):
            j1_id = j1 if isinstance(j1, int) else nuevos_ids[j1]
            j2_id = j2 if isinstance(j2, int) else nuevos_ids[j2]

            # Verificar si ya existe
            existe = s.execute(text("""
                SELECT id FROM torneos_parejas
                WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2)
                    OR (jugador1_id = :j2 AND jugador2_id = :j1))
            """), {"t": TORNEO_ID, "j1": j1_id, "j2": j2_id}).fetchone()

            if existe:
                print(f"   ⚠️  Pareja {i} ya existe (ID: {existe[0]})")
                continue

            restr_json = json.dumps(restricciones) if restricciones else None

            if restr_json:
                r = s.execute(text("""
                    INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
                    VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb))
                    RETURNING id
                """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": j1_id, "j2": j2_id, "r": restr_json})
            else:
                r = s.execute(text("""
                    INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado)
                    VALUES (:t, :c, :j1, :j2, 'confirmada')
                    RETURNING id
                """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": j1_id, "j2": j2_id})

            pid = r.fetchone()[0]
            n_restr = len(restricciones) if restricciones else 0
            print(f"   ✅ Pareja {i} (ID: {pid}) - jugadores {j1_id}/{j2_id} - {n_restr} restricción(es)")

        s.commit()

        # 3. Resumen
        total = s.execute(text(
            "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
        ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]

        print(f"\n{'=' * 70}")
        print(f"✅ LISTO - {total} parejas en 6ta del torneo {TORNEO_ID}")
        print(f"{'=' * 70}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
        s.rollback()
    finally:
        s.close()


if __name__ == "__main__":
    inscribir()
