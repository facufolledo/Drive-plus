import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    antes = c.execute(text("SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = 502")).fetchone()
    print(f"Antes: {antes[0]} {antes[1]}")
    c.execute(text("UPDATE perfil_usuarios SET apellido = 'Hrellac' WHERE id_usuario = 502"))
    c.commit()
    despues = c.execute(text("SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = 502")).fetchone()
    print(f"Después: {despues[0]} {despues[1]}")
