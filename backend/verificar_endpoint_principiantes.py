"""Verificar qué devuelve el endpoint para los principiantes"""
import requests
import json

response = requests.get("https://drive-plus-production.up.railway.app/ranking/?limit=100")
data = response.json()

jugadores = ['sebastiancorzo', 'sergiopansa', 'carlosfernandez', 'leomena10', 'jorgepaz', 'maximilianoyelamo']

print("Respuesta del endpoint de producción:")
print("=" * 60)

for j in data:
    if j.get('nombre_usuario') in jugadores:
        print(json.dumps(j, indent=2, ensure_ascii=False))
        print("-" * 40)

# También buscar cualquier jugador con partidos_ganados > 0
print("\n\nJugadores con partidos_ganados > 0 en la respuesta:")
print("=" * 60)
for j in data:
    if j.get('partidos_ganados', 0) > 0:
        print(f"{j['nombre_usuario']}: {j['partidos_jugados']}PJ, {j['partidos_ganados']}PG, tendencia={j.get('tendencia')}")
