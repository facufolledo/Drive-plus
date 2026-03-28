#!/usr/bin/env python3
"""
Inscribir parejas en categoría 8va del torneo 45.
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

TORNEO_ID = 45
CATEGORIA_NOMBRE = "8va"
CATEGORIA_GENERO = "masculino"
RATING_INICIAL = 749  # Rating inicial para 8va

# Jugadores que NO están en la app (hay que crearlos)
# Se crearán con rating 749 (8va)
NUEVOS_JUGADORES = [
    {"nombre": "Rogelio", "apellido": "Estevez", "username": "rogelio.estevez", "email": "rogelio.estevez@driveplus.temp", "sexo": "M"},
    {"nombre": "Brajan", "apellido": "Oropel", "username": "brajan.oropel", "email": "brajan.oropel@driveplus.temp", "sexo": "M"},
    {"nombre": "Jeremias", "apellido": "Colina", "username": "jeremias.colina", "email": "jeremias.colina@driveplus.temp", "sexo": "M"},
    {"nombre": "Franco", "apellido": "Colina", "username": "franco.colina", "email": "franco.colina@driveplus.temp", "sexo": "M"},
    {"nombre": "Lucas", "apellido": "Olivera", "username": "lucas.olivera.t45", "email": "lucas.olivera.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Gregori", "apellido": "Lucas", "username": "gregori.lucas", "email": "gregori.lucas@driveplus.temp", "sexo": "M"},
    {"nombre": "Maxi", "apellido": "Britos", "username": "maxi.britos.t45", "email": "maxi.britos.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Nairo", "apellido": "Salas", "username": "nairo.salas", "email": "nairo.salas@driveplus.temp", "sexo": "M"},
    {"nombre": "Martin", "apellido": "Brizuela", "username": "martin.brizuela.t45", "email": "martin.brizuela.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Santiago", "apellido": "Ceballo", "username": "santiago.ceballo", "email": "santiago.ceballo@driveplus.temp", "sexo": "M"},
    {"nombre": "Axel", "apellido": "Alfaro", "username": "axel.alfaro", "email": "axel.alfaro@driveplus.temp", "sexo": "M"},
    {"nombre": "Juan", "apellido": "Velazque", "username": "juan.velazque", "email": "juan.velazque@driveplus.temp", "sexo": "M"},
    {"nombre": "Benha", "apellido": "Alfaro", "username": "benha.alfaro", "email": "benha.alfaro@driveplus.temp", "sexo": "M"},
    {"nombre": "Federico", "apellido": "Manrique", "username": "federico.manrique", "email": "federico.manrique@driveplus.temp", "sexo": "M"},
    {"nombre": "Chilecito", "apellido": "Zaracho", "username": "chilecito.zaracho", "email": "chilecito.zaracho@driveplus.temp", "sexo": "M"},
    {"nombre": "Mercado", "apellido": "Mercado", "username": "mercado.mercado", "email": "mercado.mercado@driveplus.temp", "sexo": "M"},
    {"nombre": "Maximiliano", "apellido": "Barro", "username": "maximiliano.barro", "email": "maximiliano.barro@driveplus.temp", "sexo": "M"},
    {"nombre": "Rodrigo", "apellido": "Barros", "username": "rodrigo.barros.t45", "email": "rodrigo.barros.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Lucas", "apellido": "Almada", "username": "lucas.almada.t45", "email": "lucas.almada.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Jorge", "apellido": "Medina", "username": "jorge.medina.t45", "email": "jorge.medina.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Leandro", "apellido": "Toledo", "username": "leandro.toledo.t45", "email": "leandro.toledo.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Matias", "apellido": "Tramontin", "username": "matias.tramontin", "email": "matias.tramontin@driveplus.temp", "sexo": "M"},
    {"nombre": "Ariel", "apellido": "Calderon", "username": "ariel.calderon", "email": "ariel.calderon@driveplus.temp", "sexo": "M"},
    {"nombre": "Jere", "apellido": "Vera", "username": "jere.vera.t45", "email": "jere.vera.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Tobias", "apellido": "Cardenas", "username": "tobias.cardenas", "email": "tobias.cardenas@driveplus.temp", "sexo": "M"},
    {"nombre": "Agustin", "apellido": "Rojas", "username": "agustin.rojas.t45", "email": "agustin.rojas.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Ignacio", "apellido": "Villanova", "username": "ignacio.villanova", "email": "ignacio.villanova@driveplus.temp", "sexo": "M"},
    {"nombre": "Facundo", "apellido": "Fernandez", "username": "facundo.fernandez.t45", "email": "facundo.fernandez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Leonardo", "apellido": "Luna", "username": "leonardo.luna.t45", "email": "leonardo.luna.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Nieto", "apellido": "Boris", "username": "nieto.boris", "email": "nieto.boris@driveplus.temp", "sexo": "M"},
    {"nombre": "Agustin", "apellido": "Cortez", "username": "agustin.cortez.t45", "email": "agustin.cortez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Agustin", "apellido": "Aguilar", "username": "agustin.aguilar.t45", "email": "agustin.aguilar.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Miranda", "apellido": "Diogenes", "username": "miranda.diogenes", "email": "miranda.diogenes@driveplus.temp", "sexo": "M"},
    {"nombre": "Bautista", "apellido": "Diamante", "username": "bautista.diamante", "email": "bautista.diamante@driveplus.temp", "sexo": "M"},
    {"nombre": "Jeremias", "apellido": "Gonzalez", "username": "jeremias.gonzalez.t45", "email": "jeremias.gonzalez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Morales", "apellido": "Imanol", "username": "morales.imanol", "email": "morales.imanol@driveplus.temp", "sexo": "M"},
]

# Parejas: (jugador1, jugador2, restricciones)
# jugador = ID existente (int) o username nuevo (str)
# Restricciones = horarios en los que NO pueden jugar
PAREJAS = [
    # P1: Estevez Rogelio / Oropel Brajan - JUEVES: DESP 22:00, VIERNES: LIBRE, SÁBADO: vacío
    ("rogelio.estevez", "brajan.oropel",
     [{"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"}]),
    
    # P2: Colina Jeremias / Colina Franco - JUEVES: DESP 19:00, VIERNES: DESP 19:00, SÁBADO: vacío
    ("jeremias.colina", "franco.colina",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
     ]),
    
    # P3: Olivera Lucas / Gregori Lucas - JUEVES: DESP 20:00, VIERNES: DESP 20:00, SÁBADO: vacío
    ("lucas.olivera.t45", "gregori.lucas",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "20:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
     ]),
    
    # P4: Britos Maxi / Salas Nairo - JUEVES: DESP 19:00, VIERNES: DESP 20:00, SÁBADO: vacío
    ("maxi.britos.t45", "nairo.salas",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
     ]),
    
    # P5: Brizuela Martin / Ceballo Santiago - JUEVES: 22:00, VIERNES: DESP 22:00, SÁBADO: vacío
    ("martin.brizuela.t45", "santiago.ceballo",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"}
     ]),
    
    # P6: Alfaro Axel / Velazque Juan - JUEVES: DESDE 14 A 16 Y DESP 22, VIERNES: DESDE 14 A 16 Y DESP 22, SÁBADO: vacío
    ("axel.alfaro", "juan.velazque",
     [
         {"dias": ["jueves", "viernes"], "horaInicio": "09:00", "horaFin": "14:00"},
         {"dias": ["jueves", "viernes"], "horaInicio": "16:00", "horaFin": "22:00"}
     ]),
    
    # P7: Alfaro Benha / Manrique Federico - JUEVES: SIN PROBLEMA, VIERNES: SIN PROBLEMA, SÁBADO: vacío
    ("benha.alfaro", "federico.manrique", None),
    
    # P8: Zaracho Chilecito / Mercado Mercado - JUEVES: vacío, VIERNES: DOS PARTIDOS, SÁBADO: vacío
    ("chilecito.zaracho", "mercado.mercado", None),
    
    # P9: Barro Maximiliano / Barros Rodrigo - JUEVES: DESP 20:00, VIERNES: DESP 20:00, SÁBADO: vacío
    ("maximiliano.barro", "rodrigo.barros.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "20:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
     ]),
    
    # P10: Almada Lucas / Medina Jorge - JUEVES: 14 O 15, VIERNES: vacío, SÁBADO: vacío
    # Pueden solo de 14:00 a 15:00 jueves
    ("lucas.almada.t45", "jorge.medina.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "14:00"},
         {"dias": ["jueves"], "horaInicio": "15:00", "horaFin": "23:00"}
     ]),
    
    # P11: Toledo Leandro / Tramontin Matias - JUEVES: DESP 22:00, VIERNES: DESP 22:00, SÁBADO: DESP 14:00
    ("leandro.toledo.t45", "matias.tramontin",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "14:00"}
     ]),
    
    # P12: Calderon Ariel / Vera Jere - JUEVES: DESP 19 A 00, VIERNES: vacío, SÁBADO: vacío
    ("ariel.calderon", "jere.vera.t45",
     [{"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"}]),
    
    # P13: Cardenas Tobias / Rojas Agustin - JUEVES: vacío, VIERNES: vacío, SÁBADO: vacío (LIBRE)
    ("tobias.cardenas", "agustin.rojas.t45", None),
    
    # P14: Villanova Ignacio / Fernandez Facundo - JUEVES: vacío, VIERNES: DESP 14:00, SÁBADO: vacío
    ("ignacio.villanova", "facundo.fernandez.t45",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "14:00"}]),
    
    # P15: Luna Leonardo / Boris Nieto - JUEVES: DESP 22:00, VIERNES: DESP 22:00, SÁBADO: vacío
    ("leonardo.luna.t45", "nieto.boris",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"}
     ]),
    
    # P16: Cortez Agustin / Aguilar Agustin - JUEVES: DESP 22:01, VIERNES: DESP 22:01, SÁBADO: vacío
    ("agustin.cortez.t45", "agustin.aguilar.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:01"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:01"}
     ]),
    
    # P17: Diogenes Miranda / Diamante Bautista - JUEVES: SIN PROBLEMAS, VIERNES: SIN PROBLEMAS, SÁBADO: vacío
    ("miranda.diogenes", "bautista.diamante", None),
    
    # P18: Gonzalez Jeremias / Imanol Morales - JUEVES: DESP 22, VIERNES: DESP 22, SÁBADO: DESP 12
    ("jeremias.gonzalez.t45", "morales.imanol",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"}
     ]),
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
            print("\n💡 Categorías disponibles:")
            cats = s.execute(text(
                "SELECT id, nombre, genero FROM torneo_categorias WHERE torneo_id = :t"
            ), {"t": TORNEO_ID}).fetchall()
            for c in cats:
                print(f"   • ID {c[0]}: {c[1]} ({c[2]})")
            return
        
        CATEGORIA_ID = cat[0]
        print(f"✅ Categoría encontrada: {CATEGORIA_NOMBRE} {CATEGORIA_GENERO} (ID: {CATEGORIA_ID})")

        # 1. Crear jugadores nuevos
        nuevos_ids = {}
        print(f"\n📝 Creando {len(NUEVOS_JUGADORES)} jugadores nuevos con rating {RATING_INICIAL}...")
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

        # 3. Resumen
        total = s.execute(text(
            "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
        ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]

        print(f"\n{'=' * 70}")
        print(f"✅ LISTO - {inscritas} parejas inscritas")
        print(f"📊 Total en {CATEGORIA_NOMBRE}: {total} parejas")
        print(f"{'=' * 70}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
        s.rollback()
    finally:
        s.close()


if __name__ == "__main__":
    inscribir()
