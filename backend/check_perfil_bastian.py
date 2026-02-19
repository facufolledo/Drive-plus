"""Check perfil de Bastian"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()
u = db.execute(text("SELECT id_usuario, nombre_usuario, email, sexo, id_categoria, rating FROM usuarios WHERE id_usuario = 240")).fetchone()
print(f"Usuario: ID={u[0]}, user={u[1]}, email={u[2]}, sexo={u[3]}, cat={u[4]}, rating={u[5]}")

p = db.execute(text("SELECT * FROM perfil_usuarios WHERE id_usuario = 240")).fetchone()
if p:
    print(f"Perfil: {p}")
else:
    print("❌ NO tiene perfil en perfil_usuarios!")
db.close()
