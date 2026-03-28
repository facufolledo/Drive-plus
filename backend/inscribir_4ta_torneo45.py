#!/usr/bin/env python3
"""
Inscribir parejas en categoría 4ta del torneo 45.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45
CATEGORIA_NOMBRE = "4ta"
CATEGORIA_GENERO = "masculino"
RATING_INICIAL = 1699

# Jugadores nuevos
NUEVOS_JUGADORES = [
    {"nombre": "Axel", "apellido": "Nieto", "username": "axel.nieto.4ta.t45", "email": "axel.nieto.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Mateo", "apellido": "Gomez", "username": "mateo.gomez.t45", "email": "mateo.gomez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Merlo", "apellido": "Merlo", "username": "merlo.merlo.t45", "email": "merlo.merlo.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Franco", "apellido": "Del", "username": "franco.del.t45", "email": "franco.del.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Thiago", "apellido": "Thiago", "username": "thiago.thiago.t45", "email": "thiago.thiago.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Joaquin", "apellido": "Rivero", "username": "joaquin.rivero.4ta.t45", "email": "joaquin.rivero.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Sergio", "apellido": "Silva", "username": "sergio.silva.t45", "email": "sergio.silva.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Luis", "apellido": "Rodriguez", "username": "luis.rodriguez.4ta.t45", "email": "luis.rodriguez.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Sebastian", "apellido": "Bestani", "username": "sebastian.bestani.t45", "email": "sebastian.bestani.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Carlos", "apellido": "Gavio", "username": "carlos.gavio.t45", "email": "carlos.gavio.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Mateo", "apellido": "Diaz", "username": "mateo.diaz.4ta.t45", "email": "mateo.diaz.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Bauti", "apellido": "Sosa", "username": "bauti.sosa.t45", "email": "bauti.sosa.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Figueroa", "apellido": "Figueroa", "username": "figueroa.figueroa.4ta.t45", "email": "figueroa.figueroa.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Gomez", "apellido": "Gomez", "username": "gomez.gomez.4ta.t45", "email": "gomez.gomez.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Jere", "apellido": "Arrebola", "username": "jere.arrebola.t45", "email": "jere.arrebola.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Jere", "apellido": "Jere", "username": "jere.jere.t45", "email": "jere.jere.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Nicolas", "apellido": "Herrera", "username": "nicolas.herrera.4ta.t45", "email": "nicolas.herrera.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Kevin", "apellido": "Orellano", "username": "kevin.orellano.t45", "email": "kevin.orellano.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Bastian", "apellido": "Farran", "username": "bastian.farran.4ta.t45", "email": "bastian.farran.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Alexis", "apellido": "Maldonado", "username": "alexis.maldonado.t45", "email": "alexis.maldonado.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Juan", "apellido": "Montivero", "username": "juan.montivero.4ta.t45", "email": "juan.montivero.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Felipe", "apellido": "Juan", "username": "felipe.juan.t45", "email": "felipe.juan.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Cruz", "apellido": "Cruz", "username": "cruz.cruz.t45", "email": "cruz.cruz.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Alvaro", "apellido": "Brizuela", "username": "alvaro.brizuela.4ta.t45", "email": "alvaro.brizuela.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Agustin", "apellido": "Chumbita", "username": "agustin.chumbita.t45", "email": "agustin.chumbita.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Geronimo", "apellido": "Elizondo", "username": "geronimo.elizondo.t45", "email": "geronimo.elizondo.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Daniel", "apellido": "Chavez", "username": "daniel.chavez.t45", "email": "daniel.chavez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Juan", "apellido": "Magui", "username": "juan.magui.t45", "email": "juan.magui.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Oscar", "apellido": "Molina", "username": "oscar.molina.t45", "email": "oscar.molina.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Ale", "apellido": "Aguero", "username": "ale.aguero.t45", "email": "ale.aguero.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Hoga", "apellido": "Lois", "username": "hoga.lois.t45", "email": "hoga.lois.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Nacho", "apellido": "Villega", "username": "nacho.villega.t45", "email": "nacho.villega.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Matias", "apellido": "Gaitan", "username": "matias.gaitan.t45", "email": "matias.gaitan.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Lisandro", "apellido": "Ligorria", "username": "lisandro.ligorria.t45", "email": "lisandro.ligorria.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Brizuela", "apellido": "Brizuela", "username": "brizuela.brizuela.4ta.t45", "email": "brizuela.brizuela.4ta.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Agustin", "apellido": "Aguirre", "username": "agustin.aguirre.t45", "email": "agustin.aguirre.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Braian", "apellido": "Barrera", "username": "braian.barrera.t45", "email": "braian.barrera.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Ramiro", "apellido": "Jofre", "username": "ramiro.jofre.t45", "email": "ramiro.jofre.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Matias", "apellido": "Olivera", "username": "matias.olivera.4ta.t45", "email": "matias.olivera.4ta.t45@driveplus.temp", "sexo": "M"},
]

# Parejas: (jugador1_username, jugador2_username, restricciones)
PAREJAS = [
    ("axel.nieto.4ta.t45", "mateo.gomez.t45", []),
    ("merlo.merlo.t45", "franco.del.t45", []),
    ("thiago.thiago.t45", "joaquin.rivero.4ta.t45", []),
    ("sergio.silva.t45", "luis.rodriguez.4ta.t45", [
        {"dia": "jueves", "horaInicio": "09:00", "horaFin": "23:00"},
        {"dia": "viernes", "horaInicio": "09:00", "horaFin": "23:00"}
    ]),  # DOS PARTIDOS sábado
    ("sebastian.bestani.t45", "carlos.gavio.t45", []),
    ("mateo.diaz.4ta.t45", "bauti.sosa.t45", []),
    ("figueroa.figueroa.4ta.t45", "gomez.gomez.4ta.t45", [
        {"dia": "viernes", "horaInicio": "09:00", "horaFin": "23:00"}
    ]),  # DOS PARTIDOS jueves
    ("jere.arrebola.t45", "jere.jere.t45", []),
    ("nicolas.herrera.4ta.t45", "kevin.orellano.t45", [
        {"dia": "viernes", "horaInicio": "09:00", "horaFin": "23:00"}
    ]),  # DOS PARTIDOS jueves
    ("bastian.farran.4ta.t45", "alexis.maldonado.t45", []),
    ("juan.montivero.4ta.t45", "felipe.juan.t45", [
        {"dia": "viernes", "horaInicio": "09:00", "horaFin": "23:00"}
    ]),  # DOS PARTIDOS jueves
    ("cruz.cruz.t45", "alvaro.brizuela.4ta.t45", []),
    ("agustin.chumbita.t45", "geronimo.elizondo.t45", []),
    ("daniel.chavez.t45", "juan.magui.t45", []),
    ("oscar.molina.t45", "ale.aguero.t45", []),
    ("hoga.lois.t45", "nacho.villega.t45", []),
    ("matias.gaitan.t45", "lisandro.ligorria.t45", []),
    ("brizuela.brizuela.4ta.t45", "agustin.aguirre.t45", []),
    ("ramiro.jofre.t45", "matias.olivera.4ta.t45", [
        {"dia": "jueves", "horaInicio": "18:00", "horaFin": "23:00"},
        {"dia": "viernes", "horaInicio": "09:00", "horaFin": "21:00"}
    ]),  # Jueves: antes 18 o después 23, Viernes: después 21
]

def inscribir():
    s = Session()
    try:
        print("=" * 70)
        print(f"INSCRIBIR PAREJAS - TORNEO {TORNEO_ID} - CATEGORÍA {CATEGORIA_NOMBRE} ({CATEGORIA_GENERO})")
        print("=" * 70)

        # Obtener ID de categoría
        cat = s.execute(text("""
            SELECT id FROM torneo_categorias 
            WHERE torneo_id = :t AND nombre = :n AND genero = :g
        """), {"t": TORNEO_ID, "n": CATEGORIA_NOMBRE, "g": CATEGORIA_GENERO}).fetchone()
        
        if not cat:
            print(f"\n❌ Categoría {CATEGORIA_NOMBRE} {CATEGORIA_GENERO} no encontrada en torneo {TORNEO_ID}")
            return
        
        CATEGORIA_ID = cat[0]
        print(f"✅ Categoría encontrada: {CATEGORIA_NOMBRE} {CATEGORIA_GENERO} (ID: {CATEGORIA_ID})")

        # 1. Crear jugadores nuevos
        nuevos_ids = {}
        print(f"\n📝 Creando {len(NUEVOS_JUGADORES)} jugadores nuevos con rating {RATING_INICIAL}...")
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
            """), {"u": j["username"], "e": j["email"], "rat": RATING_INICIAL, "sex": j["sexo"]})
            uid = r.fetchone()[0]
            nuevos_ids[j["username"]] = uid

            s.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:uid, :nom, :ape, 'Córdoba', 'Argentina')
            """), {"uid": uid, "nom": j["nombre"], "ape": j["apellido"]})

            print(f"   ✅ {j['nombre']} {j['apellido']} (ID: {uid})")

        s.commit()
        print(f"   💾 {len(nuevos_ids)} jugadores creados/verificados")

        # 2. Inscribir parejas
        print(f"\n👥 Inscribiendo {len(PAREJAS)} parejas...")
        inscritas = 0
        for i, (j1, j2, restricciones) in enumerate(PAREJAS, 1):
            j1_id = j1 if isinstance(j1, int) else nuevos_ids.get(j1)
            j2_id = j2 if isinstance(j2, int) else nuevos_ids.get(j2)
            
            if not j1_id or not j2_id:
                print(f"   ❌ Pareja {i}: Jugadores no encontrados ({j1}/{j2})")
                continue

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
            restr_str = f"{n_restr} restricción(es)" if n_restr > 0 else "Sin restricciones"
            print(f"   ✅ Pareja {i} (ID: {pid}) - {restr_str}")
            inscritas += 1

        s.commit()

        print(f"\n{'=' * 70}")
        print(f"✅ LISTO - {inscritas} parejas inscritas")
        print("=" * 70)

    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    inscribir()
