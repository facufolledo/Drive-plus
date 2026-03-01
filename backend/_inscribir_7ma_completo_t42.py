"""Inscribir parejas de 7ma en T42
1. Actualizar pareja 677: Millicay/Romero Juan -> Millicay/Heredia Ezequiel
2. Inscribir 9 parejas nuevas

Horarios del torneo: vie 15:00-23:30, sáb 09:00-23:30
Restricciones = horarios en que NO pueden jugar (invertir lo que me pasaron)
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 42
CAT_ID = 106  # 7ma masculino
CAT_SISTEMA = 2  # 7ma = id_categoria 2

# Parejas a inscribir (nombre1, apellido1, nombre2, apellido2, restricciones)
# Restricciones = cuando NO pueden (invertir lo que me pasaron)
parejas_nuevas = [
    # Montivero Federico / Álvaro Díaz: pueden vie +22 -> NO pueden vie 15-22
    ("Federico", "Montivero", "Álvaro", "Díaz", [
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "22:00"}
    ]),
    # Ruarte Leandro / Ellerak Benjamin: pueden vie +20 -> NO pueden vie 15-20
    ("Leandro", "Ruarte", "Benjamin", "Hrellac", [
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "20:00"}
    ]),
    # Rodolzavich Sebastián / Sánchez Martin: pueden vie +22 -> NO pueden vie 15-22
    ("Sebastián", "Rodolzavich", "Martin", "Sánchez", [
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "22:00"}
    ]),
    # Calderón Marcos / Espejo Juan: pueden vie 16-21 -> NO pueden vie 15-16, vie 21-23:30
    ("Marcos", "Calderón", "Juan", "Espejo", [
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "16:00"},
        {"dias": ["viernes"], "horaInicio": "21:00", "horaFin": "23:30"}
    ]),
    # Alegre Franco / Gonzáles Pablo: pueden vie antes 21 -> NO pueden vie 21-23:30
    ("Franco", "Alegre", "Pablo", "Gonzáles", [
        {"dias": ["viernes"], "horaInicio": "21:00", "horaFin": "23:30"}
    ]),
    # Guerrero Facundo / Olivera Javier: pueden vie 21 -> NO pueden vie 15-21
    ("Facundo", "Guerrero", "Javier", "Olivera", [
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "21:00"}
    ]),
    # Martinez Lurdes / Carrizo Hugo: pueden vie 17-18 -> NO pueden vie 15-17, vie 18-23:30
    ("Lurdes", "Martinez", "Hugo", "Carrizo", [
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "17:00"},
        {"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "23:30"}
    ]),
    # Vega Luis / Teran Marcos: pueden vie +23 -> NO pueden vie 15-23
    ("Luis", "Vega", "Marcos", "Teran", [
        {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "23:00"}
    ]),
    # Axel Rodríguez / Alan Galvarini: pueden sáb +12 -> NO pueden sáb 09-12
    ("Axel", "Rodríguez", "Alan", "Galvarini", [
        {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "12:00"}
    ]),
]

with engine.connect() as conn:
    print("=== 1. ACTUALIZAR PAREJA 677 (Millicay/Romero -> Millicay/Heredia) ===")
    # Buscar Heredia Ezequiel
    heredia = conn.execute(text("""
        SELECT u.id_usuario FROM usuarios u
        JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE LOWER(p.nombre) LIKE '%ezequiel%' AND LOWER(p.apellido) LIKE '%heredia%'
        LIMIT 1
    """)).fetchone()
    
    if heredia:
        heredia_id = heredia[0]
        print(f"  Encontrado: Heredia Ezequiel ID:{heredia_id}")
    else:
        # Crear temp
        result = conn.execute(text("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, id_categoria, partidos_jugados)
            VALUES (:username, :email, 'temp_no_login', 1100, :cat, 0)
            RETURNING id_usuario
        """), {"username": "temp_ezequiel_heredia_t42", "email": "temp_ezequiel_heredia_t42@temp.com", "cat": CAT_SISTEMA})
        heredia_id = result.fetchone()[0]
        conn.execute(text("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
            VALUES (:uid, :nombre, :apellido)
        """), {"uid": heredia_id, "nombre": "Ezequiel", "apellido": "Heredia"})
        print(f"  Creado: Heredia Ezequiel ID:{heredia_id}")
    
    # Actualizar pareja 677
    conn.execute(text("UPDATE torneos_parejas SET jugador2_id = :new_id WHERE id = 677"), {"new_id": heredia_id})
    print(f"  ✅ Pareja 677 actualizada: Millicay (5) / Heredia ({heredia_id})")
    
    print("\n=== 2. INSCRIBIR 9 PAREJAS NUEVAS ===")
    for nom1, ape1, nom2, ape2, restricciones in parejas_nuevas:
        # Buscar o crear jugador 1
        j1 = conn.execute(text("""
            SELECT u.id_usuario FROM usuarios u
            JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE LOWER(p.nombre) LIKE :nom AND LOWER(p.apellido) LIKE :ape
            LIMIT 1
        """), {"nom": f"%{nom1.lower()}%", "ape": f"%{ape1.lower()}%"}).fetchone()
        
        if j1:
            j1_id = j1[0]
        else:
            username = f"temp_{nom1.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}_{ape1.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}_t42"
            result = conn.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, id_categoria, partidos_jugados)
                VALUES (:username, :email, 'temp_no_login', 1100, :cat, 0)
                RETURNING id_usuario
            """), {"username": username, "email": f"{username}@temp.com", "cat": CAT_SISTEMA})
            j1_id = result.fetchone()[0]
            conn.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                VALUES (:uid, :nombre, :apellido)
            """), {"uid": j1_id, "nombre": nom1, "apellido": ape1})
        
        # Buscar o crear jugador 2
        j2 = conn.execute(text("""
            SELECT u.id_usuario FROM usuarios u
            JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE LOWER(p.nombre) LIKE :nom AND LOWER(p.apellido) LIKE :ape
            LIMIT 1
        """), {"nom": f"%{nom2.lower()}%", "ape": f"%{ape2.lower()}%"}).fetchone()
        
        if j2:
            j2_id = j2[0]
        else:
            username = f"temp_{nom2.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}_{ape2.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}_t42"
            result = conn.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, id_categoria, partidos_jugados)
                VALUES (:username, :email, 'temp_no_login', 1100, :cat, 0)
                RETURNING id_usuario
            """), {"username": username, "email": f"{username}@temp.com", "cat": CAT_SISTEMA})
            j2_id = result.fetchone()[0]
            conn.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                VALUES (:uid, :nombre, :apellido)
            """), {"uid": j2_id, "nombre": nom2, "apellido": ape2})
        
        # Inscribir pareja
        result = conn.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id, categoria_id, estado, disponibilidad_horaria)
            VALUES (:tid, :j1, :j2, :cat, 'confirmada', CAST(:restr AS jsonb))
            RETURNING id
        """), {
            "tid": TORNEO_ID, "j1": j1_id, "j2": j2_id, "cat": CAT_ID,
            "restr": json.dumps(restricciones)
        })
        pareja_id = result.fetchone()[0]
        print(f"  Pareja {pareja_id}: {nom1} {ape1} ({j1_id}) / {nom2} {ape2} ({j2_id})")
    
    conn.commit()
    
    print("\n=== VERIFICACIÓN ===")
    parejas = conn.execute(text("""
        SELECT tp.id, p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios p1 ON p1.id_usuario = tp.jugador1_id
        LEFT JOIN perfil_usuarios p2 ON p2.id_usuario = tp.jugador2_id
        WHERE tp.torneo_id = 42 AND tp.categoria_id = 106
        ORDER BY tp.id
    """)).fetchall()
    for p in parejas:
        print(f"  {p[0]}: {p[1]} / {p[2]}")
    print(f"\nTotal parejas 7ma: {len(parejas)}")
    print("\n✅ Listo!")
