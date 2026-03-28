"""
Test directo contra la API de producción
"""
import requests

API_URL = "https://drive-plus-production.up.railway.app"

def test_ranking():
    print("=" * 80)
    print("TEST RANKING PRODUCCIÓN - API DIRECTA")
    print("=" * 80)
    print()
    
    url = f"{API_URL}/circuitos/zf/ranking?categoria=7ma&limit=20"
    print(f"GET {url}")
    print()
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total jugadores: {len(data)}")
            print()
            print("TOP 10:")
            print("-" * 80)
            for item in data[:10]:
                nombre = f"{item.get('nombre', '')} {item.get('apellido', '')}".strip() or item.get('nombre_usuario', 'Sin nombre')
                print(f"{item['posicion']:2d}. {nombre:40s} | {item['puntos']:5.0f} pts ({item['torneos_jugados']} torneos)")
            
            # Buscar a Montivero
            print()
            print("=" * 80)
            montivero = next((x for x in data if x['id_usuario'] == 43), None)
            if montivero:
                print(f"MONTIVERO: {montivero['puntos']} pts ({montivero['torneos_jugados']} torneos)")
            else:
                print("MONTIVERO: No encontrado en el ranking")
        else:
            print(f"Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ranking()
