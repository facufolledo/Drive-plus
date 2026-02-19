"""Fix email de Bastian en Firebase (sigue con gamail)"""
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

auth.update_user(FIREBASE_UID, email="bastianfarranquiroga@gmail.com")
user = auth.get_user(FIREBASE_UID)
print(f"✅ Email actualizado en Firebase: {user.email}")
