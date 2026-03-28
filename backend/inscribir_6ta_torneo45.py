#!/usr/bin/env python3
"""
Inscribir parejas en categoría 6ta del torneo 45.
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
CATEGORIA_NOMBRE = "6ta"
CATEGORIA_GENERO = "masculino"
RATING_INICIAL = 1299  # Rating inicial para 6ta

# Jugadores que NO están en la app (hay que crearlos)
NUEVOS_JUGADORES = [
    {"nombre": "Rodrigo", "apellido": "Tejada", "username": "rodrigo.tejada.t45", "email": "rodrigo.tejada.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Nicolas", "apellido": "Corzo", "username": "nicolas.corzo.t45", "email": "nicolas.corzo.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Ortiz", "apellido": "Ortiz", "username": "ortiz.ortiz.t45", "email": "ortiz.ortiz.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Suarez", "apellido": "Suarez", "username": "suarez.suarez.t45", "email": "suarez.suarez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Axel", "apellido": "Nieto", "username": "axel.nieto.t45", "email": "axel.nieto.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Stefy", "apellido": "Nieto", "username": "stefy.nieto.t45", "email": "stefy.nieto.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Alvaro", "apellido": "Molina", "username": "alvaro.molina.t45", "email": "alvaro.molina.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Alejo", "apellido": "Molina", "username": "alejo.molina.t45", "email": "alejo.molina.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Isaias", "apellido": "Bazan", "username": "isaias.bazan.t45", "email": "isaias.bazan.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Valentino", "apellido": "Rodriguez", "username": "valentino.rodriguez.t45", "email": "valentino.rodriguez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Ramosjuliovich", "apellido": "Ramosjuliovich", "username": "ramosjuliovich.t45", "email": "ramosjuliovich.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Stepanios", "apellido": "Yoyo", "username": "stepanios.yoyo.t45", "email": "stepanios.yoyo.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Gere", "apellido": "Fuentes", "username": "gere.fuentes.t45", "email": "gere.fuentes.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Gurgone", "apellido": "Gurgone", "username": "gurgone.gurgone.t45", "email": "gurgone.gurgone.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Cristian", "apellido": "Gurgone", "username": "cristian.gurgone.t45", "email": "cristian.gurgone.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Benjamin", "apellido": "Palacio", "username": "benjamin.palacio.t45", "email": "benjamin.palacio.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Figueroa", "apellido": "Lucas", "username": "figueroa.lucas.t45", "email": "figueroa.lucas.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Juan", "apellido": "Oliva", "username": "juan.oliva.t45", "email": "juan.oliva.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Franco", "apellido": "Leyes", "username": "franco.leyes.t45", "email": "franco.leyes.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Francisco", "apellido": "Romero", "username": "francisco.romero.t45", "email": "francisco.romero.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Fernando", "apellido": "Romero", "username": "fernando.romero.t45", "email": "fernando.romero.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Saul", "apellido": "Ontivero", "username": "saul.ontivero.t45", "email": "saul.ontivero.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Isaias", "apellido": "Ontivero", "username": "isaias.ontivero.t45", "email": "isaias.ontivero.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Fernando", "apellido": "Cordero", "username": "fernando.cordero.t45", "email": "fernando.cordero.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Cristian", "apellido": "Perez", "username": "cristian.perez.t45", "email": "cristian.perez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Jr", "apellido": "Jr", "username": "jr.jr.t45", "email": "jr.jr.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Martin", "apellido": "Sanchez", "username": "martin.sanchez.t45", "email": "martin.sanchez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Pluma", "apellido": "Arrebola", "username": "pluma.arrebola.t45", "email": "pluma.arrebola.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Lazaro", "apellido": "Ceballo", "username": "lazaro.ceballo.t45", "email": "lazaro.ceballo.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Jorge", "apellido": "Pamelin", "username": "jorge.pamelin.t45", "email": "jorge.pamelin.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Tomas", "apellido": "Cejas", "username": "tomas.cejas.t45", "email": "tomas.cejas.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Tomas", "apellido": "Redes", "username": "tomas.redes.t45", "email": "tomas.redes.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Federico", "apellido": "Llabante", "username": "federico.llabante.t45", "email": "federico.llabante.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Santiago", "apellido": "Cordoba", "username": "santiago.cordoba.t45", "email": "santiago.cordoba.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Kike", "apellido": "Santillan", "username": "kike.santillan.t45", "email": "kike.santillan.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Fabio", "apellido": "Paredes", "username": "fabio.paredes.t45", "email": "fabio.paredes.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Javier", "apellido": "Lobos", "username": "javier.lobos.t45", "email": "javier.lobos.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Mario", "apellido": "Santander", "username": "mario.santander.t45", "email": "mario.santander.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Ferreyra", "apellido": "Ferreyra", "username": "ferreyra.ferreyra.t45", "email": "ferreyra.ferreyra.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Bustos", "apellido": "Bustos", "username": "bustos.bustos.t45", "email": "bustos.bustos.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Maxi", "apellido": "Vega", "username": "maxi.vega.t45", "email": "maxi.vega.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Facundo", "apellido": "Martin", "username": "facundo.martin.t45", "email": "facundo.martin.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Juan", "apellido": "Nis", "username": "juan.nis.t45", "email": "juan.nis.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Agustin", "apellido": "Fuentes", "username": "agustin.fuentes.t45", "email": "agustin.fuentes.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Matias", "apellido": "Carrizo", "username": "matias.carrizo.t45", "email": "matias.carrizo.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Lucas", "apellido": "Juarez", "username": "lucas.juarez.t45", "email": "lucas.juarez.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Jeremias", "apellido": "Salazar", "username": "jeremias.salazar.t45", "email": "jeremias.salazar.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Jeremias", "apellido": "Charazo", "username": "jeremias.charazo.t45", "email": "jeremias.charazo.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Matias", "apellido": "Rosa", "username": "matias.rosa.t45", "email": "matias.rosa.t45@driveplus.temp", "sexo": "M"},
    {"nombre": "Miguel", "apellido": "Estrada", "username": "miguel.estrada.t45", "email": "miguel.estrada.t45@driveplus.temp", "sexo": "M"},
]

# Parejas con restricciones
PAREJAS = [
    # P1: Tejada/Corzo - J: DESP 21:00, V: POR LA MAÑANA/23HS, S: vacío
    ("rodrigo.tejada.t45", "nicolas.corzo.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "21:00"},
         {"dias": ["viernes"], "horaInicio": "12:00", "horaFin": "23:00"}
     ]),
    
    # P2: Ortiz/Suarez - J: POR LA MAÑANA/23HS, V: POR LA MAÑANA/23HS, S: vacío
    ("ortiz.ortiz.t45", "suarez.suarez.t45",
     [
         {"dias": ["jueves"], "horaInicio": "12:00", "horaFin": "23:00"},
         {"dias": ["viernes"], "horaInicio": "12:00", "horaFin": "23:00"}
     ]),
    
    # P3: Nieto Axel/Nieto Stefy - J: vacío, V: DESP 20:00, S: vacío
    ("axel.nieto.t45", "stefy.nieto.t45",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}]),
    
    # P4: Molina/Molina - J: SIN PROBLEMAS, V: SIN PROBLEMAS, S: vacío
    ("alvaro.molina.t45", "alejo.molina.t45", None),
    
    # P5: Bazan/Rodriguez - J: DESP 22:00, V: DESP 22:00, S: vacío
    ("isaias.bazan.t45", "valentino.rodriguez.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"}
     ]),
    
    # P6: Ramosjuliovich - J: vacío, V: vacío, S: vacío (FILA ROSA - IGNORAR)
    # SKIP - fila rosa
    
    # P7: Stepanios/Fuentes - J: DESP 19:00, V: DESP 19:00, S: vacío
    ("stepanios.yoyo.t45", "gere.fuentes.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
     ]),
    
    # P8: Gurgone/Gurgone - J: vacío, V: vacío, S: vacío (FILA ROSA - IGNORAR)
    # SKIP - fila rosa
    
    # P9: Gurgone Cristian/Palacio Benjamin - J: vacío, V: DESP 20:00 DOS PARTIDOS, S: vacío
    # DOS PARTIDOS viernes = NO pueden jueves
    ("cristian.gurgone.t45", "benjamin.palacio.t45",
     [{"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "23:00"}]),
    
    # P10: Figueroa Lucas - J: vacío, V: vacío, S: vacío (FILA ROSA - IGNORAR)
    # SKIP - fila rosa
    
    # P11: Oliva/Leyes - J: DESP 18:00, V: DESP 18:00, S: vacío
    ("juan.oliva.t45", "franco.leyes.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"}
     ]),
    
    # P12: Romero Francisco/Romero Fernando - J: vacío, V: DESP 17:00 DOS PARTIDOS, S: vacío
    # DOS PARTIDOS viernes = NO pueden jueves
    ("francisco.romero.t45", "fernando.romero.t45",
     [{"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "23:00"}]),
    
    # P13: Ontivero/Ontivero - J: DESP 18:00, V: DESP 20:00, S: vacío
    ("saul.ontivero.t45", "isaias.ontivero.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "20:00"}
     ]),
    
    # P14: Cordero/Perez - J: DESP 17 A 22, V: DESP 19:00, S: vacío
    ("fernando.cordero.t45", "cristian.perez.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "17:00"},
         {"dias": ["jueves"], "horaInicio": "22:00", "horaFin": "23:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
     ]),
    
    # P15: Sanchez/Arrebola - J: DOS PARTIDOS DESP 21, V: vacío, S: vacío
    ("martin.sanchez.t45", "pluma.arrebola.t45",
     [{"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "21:00"}]),
    
    # P16: Ceballo/Pamelin - J: DESP 21:00, V: DESP 21:00, S: vacío
    ("lazaro.ceballo.t45", "jorge.pamelin.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "21:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}
     ]),
    
    # P17: Cejas/Redes - J: vacío, V: DESP 18:00 DOS PARTIDOS, S: vacío
    # DOS PARTIDOS viernes = NO pueden jueves
    ("tomas.cejas.t45", "tomas.redes.t45",
     [{"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "23:00"}]),
    
    # P18: Llabante/Cordoba - J: DESP 19:00, V: DESP 19:00, S: vacío
    ("federico.llabante.t45", "santiago.cordoba.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
     ]),
    
    # P19: Santillan/Paredes - J: DEP 22:00, V: DEP 22:00, S: DESDE 14 A 15/DESP 21
    ("kike.santillan.t45", "fabio.paredes.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "14:00"},
         {"dias": ["sabado"], "horaInicio": "15:00", "horaFin": "21:00"}
     ]),
    
    # P20: Lobos/Santander - J: DESDE 18 A 22, V: DESDE 18 A 22, S: A LA MAÑANA NO
    ("javier.lobos.t45", "mario.santander.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"},
         {"dias": ["jueves"], "horaInicio": "22:00", "horaFin": "23:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"},
         {"dias": ["viernes"], "horaInicio": "22:00", "horaFin": "23:00"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"}
     ]),
    
    # P21: Ferreyra/Bustos - J: DESP 21:00, V: DESP 21:00, S: vacío
    ("ferreyra.ferreyra.t45", "bustos.bustos.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "21:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}
     ]),
    
    # P22: Vega/Martin - J: vacío, V: DESP 22:00, S: vacío
    ("maxi.vega.t45", "facundo.martin.t45",
     [{"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:00"}]),
    
    # P23: Nis/Fuentes - J: DESP 19:00, V: DESP 19:00, S: POR LA MAÑANA NO
    ("juan.nis.t45", "agustin.fuentes.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "19:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"},
         {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"}
     ]),
    
    # P24: Carrizo/Juarez - J: DESP 14:00, V: DESP 14:00, S: vacío
    ("matias.carrizo.t45", "lucas.juarez.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "14:00"},
         {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "14:00"}
     ]),
    
    # P25: Salazar/Charazo - J: DESP 18:00, V: ANTES DE 20:00, S: vacío
    ("jeremias.salazar.t45", "jeremias.charazo.t45",
     [
         {"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"},
         {"dias": ["viernes"], "horaInicio": "20:00", "horaFin": "23:00"}
     ]),
    
    # P26: Rosa/Estrada - J: DESP 18:00, V: vacío, S: vacío
    ("matias.rosa.t45", "miguel.estrada.t45",
     [{"dias": ["jueves"], "horaInicio": "09:00", "horaFin": "18:00"}]),
]


def inscribir():
    s = Session()
    try:
        print("=" * 70)
        print(f"INSCRIBIR PAREJAS - TORNEO {TORNEO_ID} - {CATEGORIA_NOMBRE}")
        print("=" * 70)

        # Obtener ID de categoría
        cat = s.execute(text("""
            SELECT id FROM torneo_categorias 
            WHERE torneo_id = :t AND nombre = :n AND genero = :g
        """), {"t": TORNEO_ID, "n": CATEGORIA_NOMBRE, "g": CATEGORIA_GENERO}).fetchone()
        
        if not cat:
            print(f"\n❌ Categoría {CATEGORIA_NOMBRE} no encontrada")
            return
        
        CATEGORIA_ID = cat[0]
        print(f"✅ Categoría: {CATEGORIA_NOMBRE} (ID: {CATEGORIA_ID})")

        # Crear jugadores
        nuevos_ids = {}
        print(f"\n📝 Creando jugadores con rating {RATING_INICIAL}...")
        for j in NUEVOS_JUGADORES:
            existe = s.execute(text(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
            ), {"u": j["username"]}).fetchone()

            if existe:
                nuevos_ids[j["username"]] = existe[0]
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

        s.commit()
        print(f"   💾 {len(nuevos_ids)} jugadores listos")

        # Inscribir parejas
        print(f"\n👥 Inscribiendo parejas...")
        inscritas = 0
        for i, (j1, j2, restricciones) in enumerate(PAREJAS, 1):
            j1_id = j1 if isinstance(j1, int) else nuevos_ids.get(j1)
            j2_id = j2 if isinstance(j2, int) else nuevos_ids.get(j2)
            
            if not j1_id or not j2_id:
                continue

            existe = s.execute(text("""
                SELECT id FROM torneos_parejas
                WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2)
                    OR (jugador1_id = :j2 AND jugador2_id = :j1))
            """), {"t": TORNEO_ID, "j1": j1_id, "j2": j2_id}).fetchone()

            if existe:
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
