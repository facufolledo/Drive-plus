"""Inscribir 11 parejas en 5ta (cat_id=108) del Torneo 42"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 42
CAT_ID = 108  # 5ta masculino
CAT_SISTEMA = 4  # 5ta = id_categoria 4

# Jugadores que ya existen (ID conocido)
existentes = {
    "Calderón Juan": 201,
    "Villegas Ignacio": 88,
    "Oliva Bautista": 200,
    "Brizuela Joaquín": 496,
    "Nieto Axel": 75,
    "Tello Sergio": 555,
    "Díaz Mateo": 500,
    "Nani Tomás": 31,
    "Loto Juan": 515,
    "Farran Bastian": 240,
    "Ruarte Leandro": 50,
}

# Jugadores que hay que crear como temporales
nuevos = [
    ("Nicolás", "Peñaloza"),
    ("Isaías", "Romero"),
    ("Martín", "Romero"),
    ("Joel", "Castro"),
    ("Gonzalo", "Aguilar"),
    ("Miguel", "Casas"),
    ("Bautista", "Sosa"),
    ("Maxi", "Abrego"),
    ("Martín", "Navarro"),
    ("Tomás", "Montiel"),
    ("Gastón", "Romero"),
]

# Parejas a inscribir: (jugador1_nombre_o_id, jugador2_nombre_o_id)
parejas = [
    ("Calderón Juan", "Villegas Ignacio"),
    ("Oliva Bautista", "Peñaloza Nicolás"),
    ("Romero Isaías", "Romero Martín"),
    ("Castro Joel", "Aguilar Gonzalo"),
    ("Brizuela Joaquín", "Casas Miguel"),
    ("Nieto Axel", "Tello Sergio"),
    ("Díaz Mateo", "Sosa Bautista"),
    ("Nani Tomás", "Abrego Maxi"),
    ("Loto Juan", "Navarro Martín"),
    ("Farran Bastian", "Montiel Tomás"),
    ("Ruarte Leandro", "Romero Gastón"),
]

# Mapeo nombre -> id (se llena con existentes + nuevos creados)
nombre_a_id = {}
# Mapeo inverso para los existentes
nombre_a_id["Calderón Juan"] = 201
nombre_a_id["Villegas Ignacio"] = 88
nombre_a_id["Oliva Bautista"] = 200
nombre_a_id["Peñaloza Nicolás"] = None  # se creará
nombre_a_id["Romero Isaías"] = None
nombre_a_id["Romero Martín"] = None
nombre_a_id["Castro Joel"] = None
nombre_a_id["Aguilar Gonzalo"] = None
nombre_a_id["Brizuela Joaquín"] = 496
nombre_a_id["Casas Miguel"] = None
nombre_a_id["Nieto Axel"] = 75
nombre_a_id["Tello Sergio"] = 555
nombre_a_id["Díaz Mateo"] = 500
nombre_a_id["Sosa Bautista"] = None
nombre_a_id["Nani Tomás"] = 31
nombre_a_id["Abrego Maxi"] = None
nombre_a_id["Loto Juan"] = 515
nombre_a_id["Navarro Martín"] = None
nombre_a_id["Farran Bastian"] = 240
nombre_a_id["Montiel Tomás"] = None
nombre_a_id["Ruarte Leandro"] = 50
nombre_a_id["Romero Gastón"] = None

# Mapeo de nombre en parejas -> (nombre_real, apellido_real) para los nuevos
nombre_a_datos = {
    "Peñaloza Nicolás": ("Nicolás", "Peñaloza"),
    "Romero Isaías": ("Isaías", "Romero"),
    "Romero Martín": ("Martín", "Romero"),
    "Castro Joel": ("Joel", "Castro"),
    "Aguilar Gonzalo": ("Gonzalo", "Aguilar"),
    "Casas Miguel": ("Miguel", "Casas"),
    "Sosa Bautista": ("Bautista", "Sosa"),
    "Abrego Maxi": ("Maxi", "Abrego"),
    "Navarro Martín": ("Martín", "Navarro"),
    "Montiel Tomás": ("Tomás", "Montiel"),
    "Romero Gastón": ("Gastón", "Romero"),
}

with engine.connect() as conn:
    # 1. Crear usuarios temporales
    print("=== CREANDO USUARIOS TEMPORALES ===")
    for nombre_key, datos in nombre_a_datos.items():
        nombre, apellido = datos
        username = f"temp_{nombre.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}_{apellido.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}_t42"
        
        # Crear usuario
        result = conn.execute(text("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, id_categoria, partidos_jugados)
            VALUES (:username, :email, 'temp_no_login', 1400, :cat, 0)
            RETURNING id_usuario
        """), {
            "username": username,
            "email": f"{username}@temp.com",
            "cat": CAT_SISTEMA
        })
        user_id = result.fetchone()[0]
        
        # Crear perfil
        conn.execute(text("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
            VALUES (:uid, :nombre, :apellido)
        """), {"uid": user_id, "nombre": nombre, "apellido": apellido})
        
        nombre_a_id[nombre_key] = user_id
        print(f"  Creado: {nombre} {apellido} -> ID:{user_id} (user:{username})")
    
    # 2. Inscribir parejas
    print("\n=== INSCRIBIENDO PAREJAS ===")
    for j1_nombre, j2_nombre in parejas:
        j1_id = nombre_a_id[j1_nombre]
        j2_id = nombre_a_id[j2_nombre]
        
        result = conn.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id, categoria_id, estado)
            VALUES (:tid, :j1, :j2, :cat, 'confirmada')
            RETURNING id
        """), {"tid": TORNEO_ID, "j1": j1_id, "j2": j2_id, "cat": CAT_ID})
        pareja_id = result.fetchone()[0]
        print(f"  Pareja {pareja_id}: {j1_nombre} (ID:{j1_id}) / {j2_nombre} (ID:{j2_id})")
    
    conn.commit()
    
    # 3. Verificar
    print("\n=== VERIFICACIÓN ===")
    parejas_db = conn.execute(text("""
        SELECT tp.id, p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios p1 ON p1.id_usuario = tp.jugador1_id
        LEFT JOIN perfil_usuarios p2 ON p2.id_usuario = tp.jugador2_id
        WHERE tp.torneo_id = 42 AND tp.categoria_id = 108
        ORDER BY tp.id
    """)).fetchall()
    for p in parejas_db:
        print(f"  Pareja {p[0]}: {p[1]} / {p[2]}")
    print(f"\nTotal parejas 5ta: {len(parejas_db)}")
    print("✅ Listo!")
