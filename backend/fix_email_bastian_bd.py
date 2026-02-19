"""Fix email de Bastian en BD solamente (Firebase ya corregido manualmente)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()
db.execute(text("UPDATE usuarios SET email = 'bastianfarranquiroga@gmail.com' WHERE id_usuario = 240"))
db.commit()
r = db.execute(text("SELECT email FROM usuarios WHERE id_usuario = 240")).fetchone()
print(f"✅ Email actualizado: {r[0]}")
db.close()
