"""Inscribir pareja en 7ma (cat_id=106) del Torneo 42
Millicay Gustavo / Romero Juan
Horarios: vie +20, sáb +20 -> NO pueden: vie 15:00-20:00, sáb 09:00-20:00
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

with engine.connect() as conn:
    # Buscar jugadores
    for nombre, apellido in [("Gustavo", "Millicay"), ("Juan", "Romero")]:
        r = conn.execute(text("""
            SELECT u.id_usuario, p.nombre, p.apellido, u.nombre_usuario, u.rating
            FROM usuarios u JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE (LOWER(p.nombre) LIKE :nom AND LOWER(p.apellido) LIKE :ap)
            ORDER BY u.id_usuario
        """), {"nom": f"%{nombre.lower()}%", "ap": f"%{apellido.lower()}%"}).fetchall()
        if r:
            for row in r:
                print(f"  Encontrado: {row[1]} {row[2]} -> ID:{row[0]} (user:{row[3]}) rating:{row[4]}")
        else:
            print(f"  ❌ {nombre} {apellido} NO ENCONTRADO")

with engine.connect() as conn:
    # Crear temporales si no existen
    nuevos = {}
    for nombre, apellido in [("Gustavo", "Millicay"), ("Juan", "Romero")]:
        r = conn.execute(text("""
            SELECT u.id_usuario FROM usuarios u
            JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE (LOWER(p.nombre) LIKE :nom AND LOWER(p.apellido) LIKE :ap)
            ORDER BY u.id_usuario LIMIT 1
        """), {"nom": f"%{nombre.lower()}%", "ap": f"%{apellido.lower()}%"}).fetchone()
        
        if r:
            nuevos[f"{apellido} {nombre}"] = r[0]
            print(f"  ✅ {nombre} {apellido} ya existe: ID {r[0]}")
        else:
            username = f"temp_{nombre.lower()}_{apellido.lower()}_t42"
            result = conn.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, id_categoria, partidos_jugados)
                VALUES (:username, :email, 'temp_no_login', 1100, :cat, 0)
                RETURNING id_usuario
            """), {"username": username, "email": f"{username}@temp.com", "cat": CAT_SISTEMA})
            uid = result.fetchone()[0]
            conn.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                VALUES (:uid, :nombre, :apellido)
            """), {"uid": uid, "nombre": nombre, "apellido": apellido})
            nuevos[f"{apellido} {nombre}"] = uid
            print(f"  Creado: {nombre} {apellido} -> ID:{uid}")
    
    j1_id = nuevos["Millicay Gustavo"]
    j2_id = nuevos["Romero Juan"]
    
    # Inscribir pareja
    result = conn.execute(text("""
        INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id, categoria_id, estado, disponibilidad_horaria)
        VALUES (:tid, :j1, :j2, :cat, 'confirmada', CAST(:restr AS jsonb))
        RETURNING id
    """), {
        "tid": TORNEO_ID, "j1": j1_id, "j2": j2_id, "cat": CAT_ID,
        "restr": json.dumps([
            {"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "20:00"},
            {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "20:00"},
        ])
    })
    pareja_id = result.fetchone()[0]
    print(f"\n  ✅ Pareja {pareja_id}: Millicay Gustavo (ID:{j1_id}) / Romero Juan (ID:{j2_id})")
    print(f"     Restricciones: NO pueden vie 15-20, sáb 09-20")
    
    conn.commit()
    print("\n✅ Inscripta en 7ma T42!")
