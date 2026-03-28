"""
Crear usuarios temporales para los faltantes de 7ma
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.production'))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

FALTANTES = [
    {"nombre": "Pablo", "apellido": "Gallardo", "puntos": 800, "fase": "subcampeon"},
    {"nombre": "Joaquín", "apellido": "Olivera", "puntos": 100, "fase": "zona"},
]

with engine.connect() as conn:
    # Obtener ID de categoría 7ma
    cat = conn.execute(text("SELECT id_categoria FROM categorias WHERE nombre = '7ma'")).fetchone()
    cat_id = cat.id_categoria if cat else None
    
    ids_creados = []
    
    for jugador in FALTANTES:
        nombre = jugador["nombre"]
        apellido = jugador["apellido"]
        usuario = f"temp_{nombre.lower()}_{apellido.lower()}_zf7ma"
        email = f"{usuario}@driveplus.temp"
        
        # Crear usuario
        result = conn.execute(text("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, id_categoria, es_administrador)
            VALUES (:usuario, :email, 'temp_hash', :cat_id, false)
            RETURNING id_usuario
        """), {
            "usuario": usuario,
            "email": email,
            "cat_id": cat_id
        })
        user_id = result.fetchone()[0]
        
        # Crear perfil
        conn.execute(text("""
            INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
            VALUES (:id, :nombre, :apellido)
        """), {
            "id": user_id,
            "nombre": nombre,
            "apellido": apellido
        })
        
        ids_creados.append({
            "id": user_id,
            "nombre": f"{nombre} {apellido}",
            "puntos": jugador["puntos"],
            "fase": jugador["fase"]
        })
        
        print(f"✅ Usuario temporal creado: ID {user_id} - {nombre} {apellido}")
    
    conn.commit()
    
    print("\n" + "=" * 80)
    print("IDs PARA AGREGAR AL SCRIPT:")
    print("=" * 80)
    for j in ids_creados:
        print(f'    {{"id_usuario": {j["id"]}, "nombre": "{j["nombre"]}", "puntos": {j["puntos"]}, "fase": "{j["fase"]}"}},')
