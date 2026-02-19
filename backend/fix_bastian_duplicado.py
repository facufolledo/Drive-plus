"""
Fix Bastian: borrar cuenta Firebase duplicada (gamail) y vincular BD con la cuenta correcta (gmail)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import credentials, auth
from src.database.config import SessionLocal
from sqlalchemy import text

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)

UID_GAMAIL = "IldgGrwSOhP4mz0nMBQpXVOrcnt2"  # duplicado con typo
UID_GMAIL = "vpEcT7fm4zcIPdMoKiK2ngo7oF03"    # cuenta correcta
USER_ID = 240

# 1. Borrar cuenta Firebase duplicada (gamail)
print("Borrando cuenta Firebase duplicada (gamail)...")
auth.delete_user(UID_GAMAIL)
print(f"  ✅ Borrado UID: {UID_GAMAIL}")

# 2. Resetear password de la cuenta correcta
print("Reseteando password de cuenta gmail...")
auth.update_user(UID_GMAIL, password="bastian10")
print(f"  ✅ Password: bastian10")

# 3. Verificar
user = auth.get_user(UID_GMAIL)
print(f"  Firebase: {user.email} (UID: {user.uid})")

# 4. Actualizar BD con el UID correcto
db = SessionLocal()
db.execute(text("UPDATE usuarios SET uid_firebase = :uid WHERE id_usuario = :id"), 
           {"uid": UID_GMAIL, "id": USER_ID})
db.commit()
r = db.execute(text("SELECT email, uid_firebase FROM usuarios WHERE id_usuario = :id"), {"id": USER_ID}).fetchone()
print(f"  BD: email={r[0]}, uid_firebase={r[1]}")
db.close()

print("\n✅ Listo! Bastian puede loguearse con bastianfarranquiroga@gmail.com / bastian10")
