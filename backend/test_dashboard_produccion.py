"""
Script para probar el endpoint /dashboard/data en producción
"""
import requests
import json

# URL de producción
BASE_URL = "https://drive-plus-production.up.railway.app"

# Token de prueba (reemplazar con un token real)
# Para obtener un token, inicia sesión en la app y copia el firebase_token de localStorage
TOKEN = input("Ingresa tu firebase_token de localStorage: ").strip()

if not TOKEN:
    print("❌ Token vacío. Abortando.")
    exit(1)

print(f"\n🔗 Probando endpoint: {BASE_URL}/dashboard/data")
print(f"🔑 Token: {TOKEN[:20]}...")

try:
    response = requests.get(
        f"{BASE_URL}/dashboard/data",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        },
        timeout=10
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Respuesta exitosa!")
        print(f"\n📈 Top Masculino: {len(data.get('top_masculino', []))} jugadores")
        print(f"📈 Top Femenino: {len(data.get('top_femenino', []))} jugadores")
        print(f"🎾 Últimos partidos: {len(data.get('ultimos_partidos', []))} partidos")
        print(f"📊 Delta semanal: {data.get('delta_semanal', 0)} pts")
        
        print("\n📋 Datos completos:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ Error {response.status_code}")
        print(f"Respuesta: {response.text}")
        
except requests.exceptions.Timeout:
    print("\n⏱️ Timeout - El servidor tardó demasiado en responder")
except requests.exceptions.ConnectionError:
    print("\n🔌 Error de conexión - No se pudo conectar al servidor")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
