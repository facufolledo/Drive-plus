"""Marcar email de Bastian como verificado en Firebase"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import credentials, auth

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)

UID = "vpEcT7fm4zcIPdMoKiK2ngo7oF03"
auth.update_user(UID, email_verified=True)
user = auth.get_user(UID)
print(f"✅ {user.email} - email_verified: {user.email_verified}")
