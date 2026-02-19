#!/usr/bin/env python3
"""
Torneo demo para presentación a cliente.
4 categorías, 15 parejas c/u, 3 canchas, restricciones random.
Usa SQL directo para evitar timeouts con Neon.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import random, json

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

NOMBRES = [
    "Martín","Lucas","Nicolás","Santiago","Matías","Tomás","Juan","Franco",
    "Agustín","Federico","Gonzalo","Sebastián","Facundo","Ignacio","Maximiliano",
    "Rodrigo","Emiliano","Lautaro","Joaquín","Alejandro","Diego","Pablo",
    "Andrés","Cristian","Damián","Ezequiel","Gabriel","Hernán","Iván","Jorge",
    "Kevin","Leonardo","Manuel","Nahuel","Oscar","Pedro","Rafael","Sergio",
    "Valentín","Walter","Bruno","Carlos","Daniel","Eduardo","Fernando",
    "Gustavo","Hugo","Julián","Leandro","Marcos","Ramiro","Tobías",
    "Ulises","Víctor","Alan","Brian","Claudio","Darío","Esteban","Fabián",
    "Germán","Héctor","Javier","Lorenzo","Mauricio","Nelson","Omar",
    "Patricio","Ricardo","Thiago","Abel","Bautista","César","Dante","Elías",
    "Felipe","Gerardo","Joel","Luis","Miguel","Octavio","Raúl","Samuel",
    "Axel","Benicio","Camilo","Dylan","Emanuel","Félix","Gael","Ian",
    "Josué","Lionel","Mateo","Oliver","Renzo","Simón","Teo","Valentino",
    "Ariel","Ciro","Enzo","Fausto","Genaro","Iñaki","Jeremías","Lisandro",
    "Máximo","Noel","Pascual","Santino","Tadeo","Uriel","Rocco","Demian",
    "Noah","Waldo","Hilario","Otto","Baltazar","Camilo B.","Félix B.","Gael B.",
    "Ian B.","Josué B.","Lionel B.","Mateo B.","Oliver B.","Renzo B."
]

APELLIDOS = [
    "González","Rodríguez","López","Martínez","García","Fernández","Pérez",
    "Sánchez","Romero","Díaz","Torres","Álvarez","Ruiz","Ramírez","Flores",
    "Acosta","Medina","Benítez","Herrera","Aguirre","Cabrera","Molina",
    "Castro","Rojas","Ortiz","Silva","Núñez","Luna","Juárez","Morales",
    "Gutiérrez","Giménez","Peralta","Sosa","Figueroa","Córdoba","Cardozo",
    "Ríos","Ojeda","Vera","Domínguez","Vega","Campos","Ledesma","Paz",
    "Villalba","Godoy","Bustos","Pereyra","Suárez","Navarro","Bravo",
    "Vargas","Lucero","Ponce","Arias","Cáceres","Mansilla","Barrios",
    "Miranda","Ramos","Contreras","Escobar","Fuentes","Maldonado","Paredes"
]

RESTRICCIONES = [
    None, None, None,
    [{"dias":["viernes"],"horaInicio":"09:00","horaFin":"19:00"}],
    [{"dias":["sabado"],"horaInicio":"09:00","horaFin":"13:00"}],
    [{"dias":["sabado"],"horaInicio":"13:00","horaFin":"17:00"}],
    [{"dias":["viernes"],"horaInicio":"09:00","horaFin":"17:00"},{"dias":["sabado"],"horaInicio":"09:00","horaFin":"13:00"}],
    [{"dias":["viernes"],"horaInicio":"20:00","horaFin":"23:00"}],
    [{"dias":["sabado"],"horaInicio":"20:00","horaFin":"23:00"}],
    [{"dias":["viernes"],"horaInicio":"09:00","horaFin":"15:00"},{"dias":["sabado"],"horaInicio":"09:00","horaFin":"15:00"}],
]

RATINGS = {"7ma":(1000,1199),"6ta":(1200,1399),"5ta":(1400,1599),"4ta":(1600,1799)}

def crear_torneo_demo():
    session = Session()
    try:
        print("=" * 70)
        print("🏆 CREANDO TORNEO DEMO")
        print("=" * 70)

        random.shuffle(NOMBRES)
        random.shuffle(APELLIDOS)

        # 1. Torneo
        horarios = json.dumps({
            "viernes": {"inicio": "09:00", "fin": "23:00"},
            "sabado": {"inicio": "09:00", "fin": "23:00"}
        })
        r = session.execute(text("""
            INSERT INTO torneos (nombre, descripcion, categoria, genero, fecha_inicio, fecha_fin, lugar, estado, creado_por, horarios_disponibles)
            VALUES ('Torneo Demo Presentación', 'Torneo demo 4 categorías 60 parejas', 'Múltiples', 'masculino',
                    '2026-02-27', '2026-02-28', 'Club Demo Padel', 'inscripcion', 2, CAST(:h AS jsonb))
            RETURNING id
        """), {"h": horarios})
        torneo_id = r.fetchone()[0]
        print(f"\n✅ Torneo creado (ID: {torneo_id})")

        # 2. Categorías
        cat_ids = {}
        for i, cat in enumerate(RATINGS.keys()):
            r = session.execute(text("""
                INSERT INTO torneo_categorias (torneo_id, nombre, genero, max_parejas, estado, orden)
                VALUES (:tid, :nombre, 'masculino', 16, 'inscripcion', :orden)
                RETURNING id
            """), {"tid": torneo_id, "nombre": cat, "orden": i})
            cat_ids[cat] = r.fetchone()[0]
            print(f"   📂 {cat} (ID: {cat_ids[cat]})")

        # 3. Canchas
        for nombre in ["Cancha 1", "Cancha 2", "Cancha 3"]:
            session.execute(text("""
                INSERT INTO torneo_canchas (torneo_id, nombre, activa) VALUES (:tid, :n, true)
            """), {"tid": torneo_id, "n": nombre})
        print("   🏟️  3 canchas creadas")

        session.commit()
        print("   💾 Torneo base commiteado")

        # 4. Usuarios y parejas (por categoría, commit parcial)
        nombre_idx = 0
        usuario_ids = []

        for cat, cat_id in cat_ids.items():
            rat_min, rat_max = RATINGS[cat]
            print(f"\n👥 {cat}: creando 15 parejas...")

            for p in range(15):
                jugador_ids = []
                for j in range(2):
                    nom = NOMBRES[nombre_idx % len(NOMBRES)].replace(" B.","")
                    ape = APELLIDOS[nombre_idx % len(APELLIDOS)]
                    nombre_idx += 1
                    uname = f"demo_{nom.lower()}_{ape.lower()}_{nombre_idx}".replace(" ","").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n")[:50]
                    email = f"demo{nombre_idx}@demo.com"
                    rating = random.randint(rat_min, rat_max)

                    r = session.execute(text("""
                        INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
                        VALUES (:u, :e, 'demo_no_login', :rat, 'M', :pj)
                        RETURNING id_usuario
                    """), {"u": uname, "e": email, "rat": rating, "pj": random.randint(0,30)})
                    uid = r.fetchone()[0]
                    jugador_ids.append(uid)
                    usuario_ids.append(uid)

                    session.execute(text("""
                        INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, telefono, fecha_nacimiento, mano_habil, ciudad, pais)
                        VALUES (:uid, :nom, :ape, :tel, :fn, :mano, :ciudad, 'Argentina')
                    """), {
                        "uid": uid, "nom": nom, "ape": ape,
                        "tel": f"351{random.randint(1000000,9999999)}",
                        "fn": f"{random.randint(1985,2003)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                        "mano": random.choice(["derecha","zurda"]),
                        "ciudad": random.choice(["Córdoba","Villa María","Río Cuarto","Carlos Paz"])
                    })

                restr = random.choice(RESTRICCIONES)
                restr_json = json.dumps(restr) if restr else None

                if restr_json:
                    session.execute(text("""
                        INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria, pago_estado)
                        VALUES (:tid, :cid, :j1, :j2, 'confirmada', CAST(:r AS jsonb), 'verificado')
                    """), {"tid": torneo_id, "cid": cat_id, "j1": jugador_ids[0], "j2": jugador_ids[1], "r": restr_json})
                else:
                    session.execute(text("""
                        INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, pago_estado)
                        VALUES (:tid, :cid, :j1, :j2, 'confirmada', 'verificado')
                    """), {"tid": torneo_id, "cid": cat_id, "j1": jugador_ids[0], "j2": jugador_ids[1]})

            session.commit()
            print(f"   ✅ {cat} lista")

        # Guardar IDs para limpieza
        with open("demo_torneo_ids.json", "w") as f:
            json.dump({"torneo_id": torneo_id, "usuario_ids": usuario_ids}, f)

        print(f"\n{'=' * 70}")
        print(f"🎉 TORNEO DEMO CREADO")
        print(f"{'=' * 70}")
        print(f"🏆 ID: {torneo_id}")
        print(f"📂 4 categorías | 👥 60 parejas | 👤 120 usuarios | 🏟️ 3 canchas")
        print(f"\n⚠️  Para eliminar: python eliminar_torneo_demo.py {torneo_id}")
        print(f"💾 IDs en demo_torneo_ids.json")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    crear_torneo_demo()
