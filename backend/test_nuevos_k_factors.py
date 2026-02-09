"""
Script para probar los nuevos K-factors sin recalcular todo
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.elo_config import EloConfig

print("\n" + "="*80)
print("NUEVOS K-FACTORS CONFIGURADOS")
print("="*80 + "\n")

print("Configuración actual de K-factors:")
print("-" * 80)

for level, config in EloConfig.K_FACTORS.items():
    max_partidos = config["max_partidos"]
    k_value = config["k_value"]
    
    if max_partidos == float('inf'):
        rango = f"51+ partidos"
    elif level == "nuevo":
        rango = f"0-{max_partidos} partidos"
    else:
        # Calcular el inicio del rango basado en el nivel anterior
        if level == "intermedio":
            inicio = EloConfig.K_FACTORS["nuevo"]["max_partidos"] + 1
        elif level == "estable":
            inicio = EloConfig.K_FACTORS["intermedio"]["max_partidos"] + 1
        else:
            inicio = EloConfig.K_FACTORS["estable"]["max_partidos"] + 1
        
        rango = f"{inicio}-{max_partidos} partidos"
    
    print(f"{level.capitalize():15} | {rango:20} | K = {k_value}")

print("-" * 80)

# Probar algunos casos
print("\n" + "="*80)
print("EJEMPLOS DE K-FACTOR POR PARTIDOS JUGADOS")
print("="*80 + "\n")

casos_prueba = [0, 1, 5, 10, 11, 15, 20, 25, 26, 30, 40, 50, 51, 60, 100]

for partidos in casos_prueba:
    k = EloConfig.get_k_factor(partidos)
    print(f"Partidos jugados: {partidos:3} → K-factor: {k}")

print("\n" + "="*80)
print("COMPARACIÓN CON CONFIGURACIÓN ANTERIOR")
print("="*80 + "\n")

# K-factors anteriores
K_FACTORS_ANTERIORES = {
    "nuevo": {"max_partidos": 5, "k_value": 200},
    "intermedio": {"max_partidos": 15, "k_value": 180},
    "estable": {"max_partidos": 40, "k_value": 20},
    "experto": {"max_partidos": float('inf'), "k_value": 15}
}

def get_k_anterior(partidos: int) -> int:
    """Obtener K-factor con configuración anterior"""
    for level, config in K_FACTORS_ANTERIORES.items():
        if partidos <= config["max_partidos"]:
            return config["k_value"]
    return K_FACTORS_ANTERIORES["experto"]["k_value"]

print(f"{'Partidos':>10} | {'K Anterior':>12} | {'K Nuevo':>10} | {'Diferencia':>12}")
print("-" * 60)

for partidos in [0, 5, 10, 15, 20, 25, 30, 40, 50, 60]:
    k_anterior = get_k_anterior(partidos)
    k_nuevo = EloConfig.get_k_factor(partidos)
    diferencia = k_nuevo - k_anterior
    signo = "+" if diferencia > 0 else ""
    
    print(f"{partidos:>10} | {k_anterior:>12} | {k_nuevo:>10} | {signo}{diferencia:>11}")

print("\n" + "="*80)
print("IMPACTO EN CAMBIOS DE RATING")
print("="*80 + "\n")

print("Ejemplo: Jugador principiante (rating 500) gana contra jugador 8va (rating 800)")
print("Expectativa de victoria: ~25%")
print("Score real: 1.0 (victoria)")
print("Sets multiplier: 1.1 (ganó 2-0)")
print("\n")

# Simular cambio de rating
from src.services.elo_service import EloService

elo_service = EloService()

# Caso 1: Jugador con 5 partidos
print("CASO 1: Jugador con 5 partidos")
print("-" * 40)

team_a = [
    {"rating": 500, "partidos": 5, "volatilidad": 1.0, "id": 1},
    {"rating": 520, "partidos": 5, "volatilidad": 1.0, "id": 2}
]

team_b = [
    {"rating": 800, "partidos": 20, "volatilidad": 1.0, "id": 3},
    {"rating": 820, "partidos": 20, "volatilidad": 1.0, "id": 4}
]

resultado = elo_service.calculate_match_ratings(
    team_a_players=team_a,
    team_b_players=team_b,
    sets_a=2,
    sets_b=0,
    games_a=12,
    games_b=4,
    match_type="torneo"
)

print(f"K-factor usado: {resultado['match_details']['team_a_k']:.1f}")
print(f"Expectativa: {resultado['match_details']['expected_a']:.2%}")
print(f"Rating antes: {team_a[0]['rating']}")
print(f"Rating después: {resultado['team_a']['players'][0]['new_rating']}")
print(f"Cambio: {resultado['team_a']['players'][0]['rating_change']:+.1f}")

# Caso 2: Jugador con 20 partidos
print("\n\nCASO 2: Jugador con 20 partidos")
print("-" * 40)

team_a[0]["partidos"] = 20
team_a[1]["partidos"] = 20

resultado2 = elo_service.calculate_match_ratings(
    team_a_players=team_a,
    team_b_players=team_b,
    sets_a=2,
    sets_b=0,
    games_a=12,
    games_b=4,
    match_type="torneo"
)

print(f"K-factor usado: {resultado2['match_details']['team_a_k']:.1f}")
print(f"Expectativa: {resultado2['match_details']['expected_a']:.2%}")
print(f"Rating antes: {team_a[0]['rating']}")
print(f"Rating después: {resultado2['team_a']['players'][0]['new_rating']}")
print(f"Cambio: {resultado2['team_a']['players'][0]['rating_change']:+.1f}")

# Caso 3: Jugador con 50 partidos
print("\n\nCASO 3: Jugador con 50 partidos")
print("-" * 40)

team_a[0]["partidos"] = 50
team_a[1]["partidos"] = 50

resultado3 = elo_service.calculate_match_ratings(
    team_a_players=team_a,
    team_b_players=team_b,
    sets_a=2,
    sets_b=0,
    games_a=12,
    games_b=4,
    match_type="torneo"
)

print(f"K-factor usado: {resultado3['match_details']['team_a_k']:.1f}")
print(f"Expectativa: {resultado3['match_details']['expected_a']:.2%}")
print(f"Rating antes: {team_a[0]['rating']}")
print(f"Rating después: {resultado3['team_a']['players'][0]['new_rating']}")
print(f"Cambio: {resultado3['team_a']['players'][0]['rating_change']:+.1f}")

print("\n" + "="*80)
print("✅ Prueba completada")
print("="*80 + "\n")
