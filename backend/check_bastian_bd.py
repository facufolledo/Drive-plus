"""Check Bastian en BD"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()
rows = db.execute(text("SELECT id_usuario, nombre_usuario, email FROM usuarios WHERE email LIKE '%bastianfarran%'")).fetchall()
for r in rows:
    print(f"ID={r[0]}, user={r[1]}, email={r[2]}")
db.close()
