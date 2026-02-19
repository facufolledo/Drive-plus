"""Buscar quién tiene el email gmail en Firebase"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import credentials, auth

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)

try:
    user = auth.get_user_by_email("bastianfarranquiroga@gmail.com")
    print(f"Email gmail -> UID: {user.uid}, email: {user.email}")
except:
    print("No existe usuario con gmail")

try:
    user2 = auth.get_user_by_email("bastianfarranquiroga@gamail.com")
    print(f"Email gamail -> UID: {user2.uid}, email: {user2.email}")
except:
    print("No existe usuario con gamail")

# Buscar en BD
from src.database.config import SessionLocal
from sqlalchemy import text
db = SessionLocal()
rows = db.execute(text("SELECT id_usuario, nombre_usuario, email, firebase_uid FROM usuarios WHERE email LIKE '%bastianfarran%'")).fetchall()
for r in rows:
    print(f"BD: ID={r[0]}, user={r[1]}, email={r[2]}, firebase_uid={r[3]}")
db.close()
