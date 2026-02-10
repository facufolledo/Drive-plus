import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env.production')

API_URL = "https://drive-plus-production.up.railway.app"

try:
    # Llamar al endpoint de ranking
    response = requests.get(f"{API_URL}/ranking/?limit=10")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Respuesta exitosa del endpoint:\n")
        
        for i, jugador in enumerate(data[:5], 1):
            print(f"{i}. {jugador.get('nombre')} {jugador.get('apellido')}")
            print(f"   Rating: {jugador.get('rating')}")
            print(f"   Partidos jugados: {jugador.get('partidos_jugados')}")
            print(f"   Partidos ganados: {jugador.get('partidos_ganados')}")
            
            # Calcular winrate
            pj = jugador.get('partidos_jugados', 0)
            pg = jugador.get('partidos_ganados', 0)
            winrate = round((pg / pj * 100) if pj > 0 else 0)
            print(f"   Winrate: {winrate}%")
            print(f"   Tendencia: {jugador.get('tendencia')}")
            print()
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
