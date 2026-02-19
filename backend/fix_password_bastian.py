"""Reset password de Bastian en Firebase"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import credentials, auth

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)

FIREBASE_UID = "IldgGrwSOhP4mz0nMBQpXVOrcnt2"

# Verificar estado actual
user = auth.get_user(FIREBASE_UID)
print(f"Email en Firebase: {user.email}")
print(f"UID: {user.uid}")

# Resetear password
auth.update_user(FIREBASE_UID, password="bastian10")
print("✅ Password reseteada a: bastian10")
