"""
Probar el endpoint de ranking y mostrar la respuesta JSON completa
"""
import requests
import json

BASE_URL = "https://drive-plus-production.up.railway.app"

print("=" * 60)
print("PROBANDO ENDPOINT DE RANKING - RESPUESTA COMPLETA")
print("=" * 60)

# Obtener ranking
response = requests.get(f"{BASE_URL}/ranking/?limit=100")

if response.status_code != 200:
    print(f"❌ Error: Status {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()

print(f"\n✅ Respuesta exitosa - {len(data)} jugadores")
print("\nPrimeros 3 jugadores con partidos:")
print("=" * 60)

jugadores_con_partidos = [j for j in data if j.get('partidos_jugados', 0) > 0]

for i, jugador in enumerate(jugadores_con_partidos[:3], 1):
    print(f"\n{i}. JSON completo:")
    print(json.dumps(jugador, indent=2, ensure_ascii=False))
    print("-" * 60)

print("\n" + "=" * 60)
print("VERIFICACIÓN DE CAMPOS")
print("=" * 60)

for jugador in jugadores_con_partidos[:5]:
    nombre = jugador.get('nombre_usuario', 'N/A')
    pj = jugador.get('partidos_jugados', 'MISSING')
    pg = jugador.get('partidos_ganados', 'MISSING')
    
    print(f"{nombre}: partidos_jugados={pj}, partidos_ganados={pg}")
    
    if pg == 'MISSING':
        print(f"  ⚠️  Campo 'partidos_ganados' NO EXISTE en la respuesta")
    elif pg == 0 and pj > 0:
        print(f"  ⚠️  Tiene {pj} partidos pero 0 victorias")
