"""
Test directo del endpoint de producción
"""
import requests
import json

print("Probando endpoint de producción...")
print("=" * 60)

response = requests.get("https://drive-plus-production.up.railway.app/ranking/?limit=100")

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()

# Buscar jugadores específicos que sabemos tienen partidos
jugadores_test = ['coppedejoaco', 'cristiancampos', 'nahuelmolina']

print("\nJugadores con partidos:")
for jugador in data:
    if jugador.get('nombre_usuario') in jugadores_test:
        print(f"\n{jugador.get('nombre_usuario')}:")
        print(f"  partidos_jugados: {jugador.get('partidos_jugados')}")
        print(f"  partidos_ganados: {jugador.get('partidos_ganados')}")
        print(f"  tendencia: {jugador.get('tendencia')}")
        
        if jugador.get('partidos_ganados') == 0 and jugador.get('partidos_jugados') > 0:
            print("  ❌ PROBLEMA: Debería tener victorias")
        elif jugador.get('partidos_ganados') > 0:
            print("  ✅ OK: Tiene victorias")
