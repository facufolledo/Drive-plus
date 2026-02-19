"""Fix email de Bastian Farran Quiroga: gamail -> gmail"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import credentials, auth
from src.database.config import SessionLocal
from sqlalchemy import text

# Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)

EMAIL_VIEJO = "bastianfarranquiroga@gamail.com"
EMAIL_NUEVO = "bastianfarranquiroga@gmail.com"
FIREBASE_UID = "IldgGrwSOhP4mz0nMBQpXVOrcnt2"
USER_ID = 240

# 1. Actualizar en Firebase
print("Actualizando email en Firebase...")
auth.update_user(FIREBASE_UID, email=EMAIL_NUEVO)
print(f"  ✅ Firebase: {EMAIL_VIEJO} -> {EMAIL_NUEVO}")

# 2. Actualizar en BD
db = SessionLocal()
db.execute(text("UPDATE usuarios SET email = :nuevo WHERE id_usuario = :uid"), 
           {"nuevo": EMAIL_NUEVO, "uid": USER_ID})
db.commit()
print(f"  ✅ BD: email actualizado para usuario {USER_ID}")

db.close()
print(f"\n✅ Listo! Email corregido a {EMAIL_NUEVO}")
