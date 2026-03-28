#!/usr/bin/env python3
"""
Inscribir parejas en categoría 3ra del torneo 45.
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
CATEGORIA_NOMBRE = "3ra"
CATEGORIA_GENERO = "masculino"
RATING_INICIAL = 1899

# Jugadores nuevos (solo los que no están en el sistema)
NUEVOS_JUGADORES = [
    {"nombre": "Carlos", "apellido": "Gudiño", "username": "carlos.gudino.t45", "email": "carlos.gudino.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Busleiman", "apellido": "Busleiman", "username": "busleiman.busleiman.t45", "email": "busleiman.busleiman.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Olarte", "apellido": "Chayle", "username": "olarte.chayle.t45", "email": "olarte.chayle.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Simon", "apellido": "Grande", "username": "simon.grande.t45", "email": "simon.grande.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Dario", "apellido": "Ruarte", "username": "dario.ruarte.t45", "email": "dario.ruarte.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Benja", "apellido": "Rojo", "username": "benja.rojo.t45", "email": "benja.rojo.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Bustos", "apellido": "Bustos", "username": "bustos.bustos.t45", "email": "bustos.bustos.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Edebercha", "apellido": "Edebercha", "username": "edebercha.edebercha.t45", "email": "edebercha.edebercha.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Suarez", "apellido": "Suarez", "username": "suarez.suarez.3ra.t45", "email": "suarez.suarez.3ra.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Lucas", "apellido": "Alcaraz", "username": "lucas.alcaraz.t45", "email": "lucas.alcaraz.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Facundo", "apellido": "Paredes", "username": "facundo.paredes.t45", "email": "facundo.paredes.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Marcelo", "apellido": "Bordon", "username": "marcelo.bordon.t45", "email": "marcelo.bordon.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Luciano", "apellido": "Luna", "username": "luciano.luna.t45", "email": "luciano.luna.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Maxi", "apellido": "Paredes", "username": "maxi.paredes.t45", "email": "maxi.paredes.t45@driveplus.temp", "sexo": "M"},
]

# Jugadores que ya existen en el sistema (buscar por username similar)
JUGADORES_EXISTENTES = [
    "santiago.ceballo",  # Cristian Ceballo
    "jere.arrebola",     # Jere Arrebola
    "kevin.gurgone",     # Kevin Gurgone  
    "matias.olivera",    # Matias Olivera
    "juan.magui",        # Juan Magui
    "pablo.ferreyra",    # Pablo Ferreyra
]

# Parejas: (jugador1_username, jugador2_username, restricciones)
PAREJAS = [
    ("carlos.gudino.t45", "busleiman.busleiman.t45", [
        {"dia": "viernes", "horaInicio": "09:00", "horaFin": "15:00"},
        {"dia": "viernes", "horaInicio": "15:01", "horaFin": "23:00"},
        {"dia": "viernes", "horaInicio": "23:01", "horaFin": "23:59"}
    ]),  # Solo pueden viernes 15:00 y 23:00
    ("olarte.chayle.t45", "simon.grande.t45", [
        {"dia": "jueves", "horaInicio": "09:00", "horaFin": "23:00"}
    ]),  # DOS PARTIDOS → NO pueden jueves
    ("santiago.ceballo", "dario.ruarte.t45", [
        {"dia": "viernes", "horaInicio": "09:00", "horaFin": "19:00"},
        {"dia": "sabado", "horaInicio": "09:00", "horaFin": "18:00"}
    ]),  # Viernes DESP 19, Sábado DESP 18
    ("jere.arrebola", "benja.rojo.t45", []),
    ("kevin.gurgone", "matias.olivera", [
        {"dia": "viernes", "horaInicio": "09:00", "horaFin": "19:00"}
    ]),  # Viernes DESP 19:00
    ("juan.magui", "pablo.ferreyra", []),  # Ignoro "VER ESTA EN 4TA"
    ("bustos.bustos.t45", "edebercha.edebercha.t45", []),
    ("suarez.suarez.3ra.t45", "lucas.alcaraz.t45", []),
    ("facundo.paredes.t45", "marcelo.bordon.t45", []),
    ("luciano.luna.t45", "maxi.paredes.t45", []),
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

        # 1. Buscar jugadores existentes
        jugadores_ids = {}
        print(f"\n🔍 Buscando jugadores existentes...")
        for username in JUGADORES_EXISTENTES:
            existe = s.execute(text(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario LIKE :u"
            ), {"u": f"%{username}%"}).fetchone()
            
            if existe:
                jugadores_ids[username] = existe[0]
                print(f"   ✅ {username} encontrado (ID: {existe[0]})")
            else:
                print(f"   ⚠️  {username} NO encontrado")

        # 2. Crear jugadores nuevos
        print(f"\n📝 Creando {len(NUEVOS_JUGADORES)} jugadores nuevos con rating {RATING_INICIAL}...")
        for j in NUEVOS_JUGADORES:
            existe = s.execute(text(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
            ), {"u": j["username"]}).fetchone()

            if existe:
                jugadores_ids[j["username"]] = existe[0]
                print(f"   ⚠️  {j['nombre']} {j['apellido']} ya existe (ID: {existe[0]})")
                continue

            r = s.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
                VALUES (:u, :e, 'temp_no_login', :rat, :sex, 0)
                RETURNING id_usuario
            """), {"u": j["username"], "e": j["email"], "rat": RATING_INICIAL, "sex": j["sexo"]})
            uid = r.fetchone()[0]
            jugadores_ids[j["username"]] = uid

            s.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:uid, :nom, :ape, 'Córdoba', 'Argentina')
            """), {"uid": uid, "nom": j["nombre"], "ape": j["apellido"]})

            print(f"   ✅ {j['nombre']} {j['apellido']} (ID: {uid})")

        s.commit()
        print(f"   💾 Total jugadores: {len(jugadores_ids)}")

        # 3. Inscribir parejas
        print(f"\n👥 Inscribiendo {len(PAREJAS)} parejas...")
        inscritas = 0
        for i, (j1, j2, restricciones) in enumerate(PAREJAS, 1):
            j1_id = j1 if isinstance(j1, int) else jugadores_ids.get(j1)
            j2_id = j2 if isinstance(j2, int) else jugadores_ids.get(j2)
            
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
