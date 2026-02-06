"""
Test directo al endpoint de parejas del torneo 37
"""
import requests
import json

# URL del backend
BASE_URL = "http://localhost:8000"

def test_endpoint():
    url = f"{BASE_URL}/torneos/37/parejas"
    
    print("=" * 80)
    print(f"GET {url}")
    print("=" * 80)
    
    response = requests.get(url)
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        parejas = response.json()
        print(f"\nTotal parejas: {len(parejas)}")
        
        # Mostrar primeras 3 parejas
        for i, pareja in enumerate(parejas[:3]):
            print(f"\n--- Pareja {i+1} ---")
            print(f"ID: {pareja.get('id')}")
            print(f"Nombre: {pareja.get('nombre_pareja')}")
            print(f"Estado: {pareja.get('estado')}")
            print(f"disponibilidad_horaria presente: {'disponibilidad_horaria' in pareja}")
            if 'disponibilidad_horaria' in pareja:
                print(f"disponibilidad_horaria valor: {pareja.get('disponibilidad_horaria')}")
            else:
                print("❌ Campo disponibilidad_horaria NO está en la respuesta")
            print(f"\nCampos completos: {list(pareja.keys())}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_endpoint()
