"""Crear nueva zona en 6ta con 3 parejas y 3 partidos"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 38
CATEGORIA_ID = 88  # 6ta

# Jugadores existentes:
# Juan Calderón = 201, Marcos Calderón = 216
# Farid Quiroz = 529, Nicolas Soria = 528
# Diego Martinez y Ezequiel Ceballos = crear temp

# Parejas:
# Calderón: Juan(201) + Marcos(216)
# Martinez: Diego(nuevo) + Ceballos Ezequiel(nuevo)
# Quiroz: Farid(529) + Soria Nicolas(528)

# Partidos vie 20/02:
# Calderón vs Martinez 15:00 -> Cancha 5 (libre)
# Martinez vs Quiroz 18:00 -> Cancha 8 (nueva, solo para este partido)
# Quiroz vs Calderón 21:00 -> Cancha 5 (libre con 50min)

with engine.connect() as c:
    # 1. Crear Cancha 8
    print("1. Creando Cancha 8...")
    existe = c.execute(text(
        "SELECT id FROM torneo_canchas WHERE torneo_id = :t AND nombre = 'Cancha 8'"
    ), {"t": TORNEO_ID}).fetchone()
    if existe:
        cancha8_id = existe[0]
        print(f"   Ya existe: ID {cancha8_id}")
    else:
        r = c.execute(text(
            "INSERT INTO torneo_canchas (torneo_id, nombre, activa) VALUES (:t, 'Cancha 8', true) RETURNING id"
        ), {"t": TORNEO_ID})
        cancha8_id = r.fetchone()[0]
        print(f"   Creada: ID {cancha8_id}")
    c.commit()

    # 2. Crear jugadores temp
    print("\n2. Creando jugadores temp...")
    nuevos = [
        {"nombre": "Diego", "apellido": "Martinez", "username": "diego.martinez.6ta", "email": "diego.martinez.6ta@driveplus.temp"},
        {"nombre": "Ezequiel", "apellido": "Ceballos", "username": "ezequiel.ceballos", "email": "ezequiel.ceballos@driveplus.temp"},
    ]
    nuevos_ids = {}
    for j in nuevos:
        existe = c.execute(text(
            "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
        ), {"u": j["username"]}).fetchone()
        if existe:
            nuevos_ids[j["username"]] = existe[0]
            print(f"   Ya existe: {j['nombre']} {j['apellido']} ID={existe[0]}")
        else:
            r = c.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
                VALUES (:u, :e, 'temp_no_login', 1299, 'M', 0) RETURNING id_usuario
            """), {"u": j["username"], "e": j["email"]})
            uid = r.fetchone()[0]
            nuevos_ids[j["username"]] = uid
            c.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:uid, :nom, :ape, 'Córdoba', 'Argentina')
            """), {"uid": uid, "nom": j["nombre"], "ape": j["apellido"]})
            print(f"   Creado: {j['nombre']} {j['apellido']} ID={uid}")
    c.commit()

    diego_id = nuevos_ids["diego.martinez.6ta"]
    ezequiel_id = nuevos_ids["ezequiel.ceballos"]

    # 3. Inscribir 3 parejas en 6ta
    print("\n3. Inscribiendo parejas...")
    parejas_data = [
        (201, 216, "Calderón"),      # Juan + Marcos
        (diego_id, ezequiel_id, "Martinez"),  # Diego + Ezequiel
        (529, 528, "Quiroz"),         # Farid + Nicolas
    ]
    pareja_ids = {}
    for j1, j2, nombre in parejas_data:
        existe = c.execute(text("""
            SELECT id FROM torneos_parejas
            WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2) OR (jugador1_id = :j2 AND jugador2_id = :j1))
        """), {"t": TORNEO_ID, "j1": j1, "j2": j2}).fetchone()
        if existe:
            pareja_ids[nombre] = existe[0]
            print(f"   Ya existe: {nombre} ID={existe[0]}")
        else:
            r = c.execute(text("""
                INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
                VALUES (:t, :c, :j1, :j2, 'confirmada', '[]'::jsonb) RETURNING id
            """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": j1, "j2": j2})
            pid = r.fetchone()[0]
            pareja_ids[nombre] = pid
            print(f"   Creada: {nombre} ID={pid}")
    c.commit()

    # 4. Crear zona
    print("\n4. Creando zona...")
    # Contar zonas existentes en 6ta para nombrar
    zonas_6ta = c.execute(text(
        "SELECT COUNT(*) FROM torneo_zonas WHERE torneo_id = :t AND categoria_id = :c"
    ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]
    zona_letra = chr(ord('A') + zonas_6ta)  # siguiente letra
    zona_nombre = f"Zona {zona_letra}"

    r = c.execute(text("""
        INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden) VALUES (:t, :c, :n, :o) RETURNING id
    """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "n": zona_nombre, "o": zonas_6ta + 1})
    zona_id = r.fetchone()[0]
    print(f"   Zona '{zona_nombre}' creada ID={zona_id}")

    # Asignar parejas a zona
    for nombre, pid in pareja_ids.items():
        c.execute(text("INSERT INTO torneo_zona_parejas (zona_id, pareja_id) VALUES (:z, :p)"),
                  {"z": zona_id, "p": pid})
        print(f"   Pareja {nombre} ({pid}) asignada a {zona_nombre}")
    c.commit()

    # 5. Crear partidos
    print("\n5. Creando partidos...")
    cancha5_id = 76
    partidos = [
        # Calderón vs Martinez - vie 15:00 Cancha 5
        (pareja_ids["Calderón"], pareja_ids["Martinez"], "2026-02-20 15:00:00", cancha5_id, "Calderón vs Martinez 15:00 C5"),
        # Martinez vs Quiroz - vie 18:00 Cancha 8
        (pareja_ids["Martinez"], pareja_ids["Quiroz"], "2026-02-20 18:00:00", cancha8_id, "Martinez vs Quiroz 18:00 C8"),
        # Quiroz vs Calderón - vie 21:00 Cancha 5
        (pareja_ids["Quiroz"], pareja_ids["Calderón"], "2026-02-20 21:00:00", cancha5_id, "Quiroz vs Calderón 21:00 C5"),
    ]
    for p1, p2, fecha, cancha, desc in partidos:
        r = c.execute(text("""
            INSERT INTO partidos (id_torneo, categoria_id, pareja1_id, pareja2_id, fecha_hora, cancha_id, zona_id, estado, fase)
            VALUES (:t, :c, :p1, :p2, :f, :ch, :z, 'pendiente', 'grupos') RETURNING id_partido
        """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "p1": p1, "p2": p2, "f": fecha, "ch": cancha, "z": zona_id})
        pid = r.fetchone()[0]
        print(f"   P{pid}: {desc}")
    c.commit()

    print("\n✅ LISTO - Nueva zona en 6ta creada con 3 parejas y 3 partidos")
