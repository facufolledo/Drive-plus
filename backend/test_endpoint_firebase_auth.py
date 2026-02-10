import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env.production')

API_URL = "http://localhost:8000"

# Necesitas obtener tu token de Firebase del localStorage del navegador
# Abre la consola del navegador y ejecuta: localStorage.getItem('firebase_token')
FIREBASE_TOKEN = input("Pega tu firebase_token aquí: ").strip()

if not FIREBASE_TOKEN:
    print("❌ Token no proporcionado")
    exit(1)

try:
    # Llamar al endpoint de autenticación
    response = requests.post(
        f"{API_URL}/auth/firebase-auth",
        json={"firebase_token": FIREBASE_TOKEN},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Respuesta exitosa del endpoint:")
        print(f"\n📋 Datos del usuario:")
        print(f"   ID: {data.get('id_usuario')}")
        print(f"   Username: {data.get('nombre_usuario')}")
        print(f"   Email: {data.get('email')}")
        print(f"   Nombre: {data.get('nombre')} {data.get('apellido')}")
        print(f"   Rating: {data.get('rating')}")
        print(f"   Es Administrador: {data.get('es_administrador')}")
        print(f"   Puede Crear Torneos: {data.get('puede_crear_torneos')}")
        
        if not data.get('es_administrador'):
            print("\n⚠️  El campo 'es_administrador' es False o no está presente")
        else:
            print("\n✅ El campo 'es_administrador' está en True")
            
        print(f"\n📦 JSON completo:")
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
