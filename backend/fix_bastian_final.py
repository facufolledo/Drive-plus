"""
Fix final Bastian: borrar cuenta Firebase sobrante (gmail) y crear una nueva limpia
vinculada al usuario 240 de la BD.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import credentials, auth

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)

UID_GMAIL = "vpEcT7fm4zcIPdMoKiK2ngo7oF03"

# 1. Borrar la cuenta gmail que se registró sola
print("Borrando cuenta Firebase gmail sobrante...")
auth.delete_user(UID_GMAIL)
print(f"  ✅ Borrado UID: {UID_GMAIL}")

# 2. Crear cuenta nueva limpia
print("Creando cuenta Firebase nueva...")
new_user = auth.create_user(
    email="bastianfarranquiroga@gmail.com",
    password="bastian10",
    email_verified=True
)
print(f"  ✅ Creada: UID={new_user.uid}, email={new_user.email}, verified={new_user.email_verified}")
print(f"\n✅ Bastian puede loguearse con bastianfarranquiroga@gmail.com / bastian10")
