"""
Crear usuario temporal para Montiel Nazareno
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.production'))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Obtener ID de categoría 5ta
    cat = conn.execute(text("SELECT id_categoria FROM categorias WHERE nombre = '5ta'")).fetchone()
    cat_id = cat.id_categoria if cat else None
    
    # Crear usuario
    result = conn.execute(text("""
        INSERT INTO usuarios (nombre_usuario, email, password_hash, id_categoria, es_administrador)
        VALUES (:usuario, :email, 'temp_hash', :cat_id, false)
        RETURNING id_usuario
    """), {
        "usuario": "temp_montiel_nazareno_zf5ta",
        "email": "temp_montiel_nazareno_zf5ta@driveplus.temp",
        "cat_id": cat_id
    })
    user_id = result.fetchone()[0]
    
    # Crear perfil
    conn.execute(text("""
        INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
        VALUES (:id, :nombre, :apellido)
    """), {
        "id": user_id,
        "nombre": "Nazareno",
        "apellido": "Montiel"
    })
    
    conn.commit()
    print(f"✅ Usuario temporal creado: ID {user_id} - Nazareno Montiel")
