"""
Test para verificar que jugadores principiantes suben ~50 puntos por victoria
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.elo_service import EloService

elo_service = EloService()

print("\n" + "="*80)
print("TEST: JUGADOR PRINCIPIANTE SUBE ~50 PUNTOS POR VICTORIA")
print("="*80 + "\n")

# Escenario 1: Principiante (500) vs Principiante (500) - partido parejo
print("ESCENARIO 1: Principiante vs Principiante (partido parejo)")
print("-" * 80)

team_a = [
    {"rating": 500, "partidos": 5, "volatilidad": 1.0, "id": 1},
    {"rating": 500, "partidos": 5, "volatilidad": 1.0, "id": 2}
]

team_b = [
    {"rating": 500, "partidos": 5, "volatilidad": 1.0, "id": 3},
    {"rating": 500, "partidos": 5, "volatilidad": 1.0, "id": 4}
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

print(f"Jugador A: Rating {team_a[0]['rating']} → {resultado['team_a']['players'][0]['new_rating']}")
print(f"Cambio: {resultado['team_a']['players'][0]['rating_change']:+.1f} puntos")
print(f"K-factor usado: {resultado['match_details']['team_a_k']:.1f}")
print(f"Expectativa: {resultado['match_details']['expected_a']:.1%}")

# Escenario 2: Principiante (400) vs 8va (800) - underdog gana
print("\n\nESCENARIO 2: Principiante (underdog) gana contra 8va")
print("-" * 80)

team_a = [
    {"rating": 400, "partidos": 3, "volatilidad": 1.0, "id": 1},
    {"rating": 420, "partidos": 3, "volatilidad": 1.0, "id": 2}
]

team_b = [
    {"rating": 800, "partidos": 20, "volatilidad": 1.0, "id": 3},
    {"rating": 820, "partidos": 20, "volatilidad": 1.0, "id": 4}
]

resultado = elo_service.calculate_match_ratings(
    team_a_players=team_a,
    team_b_players=team_b,
    sets_a=2,
    sets_b=1,
    games_a=13,
    games_b=11,
    match_type="torneo"
)

print(f"Jugador Principiante: Rating {team_a[0]['rating']} → {resultado['team_a']['players'][0]['new_rating']}")
print(f"Cambio: {resultado['team_a']['players'][0]['rating_change']:+.1f} puntos ⭐")
print(f"K-factor usado: {resultado['match_details']['team_a_k']:.1f}")
print(f"Expectativa: {resultado['match_details']['expected_a']:.1%}")

# Escenario 3: Principiante (300) vs Principiante (350) - victoria ajustada
print("\n\nESCENARIO 3: Principiante (300) gana contra Principiante (350)")
print("-" * 80)

team_a = [
    {"rating": 300, "partidos": 2, "volatilidad": 1.0, "id": 1},
    {"rating": 310, "partidos": 2, "volatilidad": 1.0, "id": 2}
]

team_b = [
    {"rating": 350, "partidos": 4, "volatilidad": 1.0, "id": 3},
    {"rating": 360, "partidos": 4, "volatilidad": 1.0, "id": 4}
]

resultado = elo_service.calculate_match_ratings(
    team_a_players=team_a,
    team_b_players=team_b,
    sets_a=2,
    sets_b=0,
    games_a=12,
    games_b=5,
    match_type="torneo"
)

print(f"Jugador A: Rating {team_a[0]['rating']} → {resultado['team_a']['players'][0]['new_rating']}")
print(f"Cambio: {resultado['team_a']['players'][0]['rating_change']:+.1f} puntos")
print(f"K-factor usado: {resultado['match_details']['team_a_k']:.1f}")
print(f"Expectativa: {resultado['match_details']['expected_a']:.1%}")

# Escenario 4: Principiante pierde contra otro principiante
print("\n\nESCENARIO 4: Principiante (500) pierde contra Principiante (500)")
print("-" * 80)

team_a = [
    {"rating": 500, "partidos": 5, "volatilidad": 1.0, "id": 1},
    {"rating": 500, "partidos": 5, "volatilidad": 1.0, "id": 2}
]

team_b = [
    {"rating": 500, "partidos": 5, "volatilidad": 1.0, "id": 3},
    {"rating": 500, "partidos": 5, "volatilidad": 1.0, "id": 4}
]

resultado = elo_service.calculate_match_ratings(
    team_a_players=team_a,
    team_b_players=team_b,
    sets_a=0,
    sets_b=2,
    games_a=4,
    games_b=12,
    match_type="torneo"
)

print(f"Jugador A: Rating {team_a[0]['rating']} → {resultado['team_a']['players'][0]['new_rating']}")
print(f"Cambio: {resultado['team_a']['players'][0]['rating_change']:+.1f} puntos")
print(f"K-factor usado: {resultado['match_details']['team_a_k']:.1f}")
print(f"Expectativa: {resultado['match_details']['expected_a']:.1%}")

# Escenario 5: Principiante con muchos partidos (15)
print("\n\nESCENARIO 5: Principiante con 15 partidos gana")
print("-" * 80)

team_a = [
    {"rating": 600, "partidos": 15, "volatilidad": 1.0, "id": 1},
    {"rating": 620, "partidos": 15, "volatilidad": 1.0, "id": 2}
]

team_b = [
    {"rating": 700, "partidos": 20, "volatilidad": 1.0, "id": 3},
    {"rating": 720, "partidos": 20, "volatilidad": 1.0, "id": 4}
]

resultado = elo_service.calculate_match_ratings(
    team_a_players=team_a,
    team_b_players=team_b,
    sets_a=2,
    sets_b=0,
    games_a=12,
    games_b=6,
    match_type="torneo"
)

print(f"Jugador A: Rating {team_a[0]['rating']} → {resultado['team_a']['players'][0]['new_rating']}")
print(f"Cambio: {resultado['team_a']['players'][0]['rating_change']:+.1f} puntos")
print(f"K-factor usado: {resultado['match_details']['team_a_k']:.1f}")
print(f"Expectativa: {resultado['match_details']['expected_a']:.1%}")

# Escenario 6: Principiante con 20 partidos (ya no es "nuevo")
print("\n\nESCENARIO 6: Principiante con 20 partidos gana (nivel intermedio)")
print("-" * 80)

team_a = [
    {"rating": 700, "partidos": 20, "volatilidad": 1.0, "id": 1},
    {"rating": 720, "partidos": 20, "volatilidad": 1.0, "id": 2}
]

team_b = [
    {"rating": 800, "partidos": 30, "volatilidad": 1.0, "id": 3},
    {"rating": 820, "partidos": 30, "volatilidad": 1.0, "id": 4}
]

resultado = elo_service.calculate_match_ratings(
    team_a_players=team_a,
    team_b_players=team_b,
    sets_a=2,
    sets_b=1,
    games_a=13,
    games_b=11,
    match_type="torneo"
)

print(f"Jugador A: Rating {team_a[0]['rating']} → {resultado['team_a']['players'][0]['new_rating']}")
print(f"Cambio: {resultado['team_a']['players'][0]['rating_change']:+.1f} puntos")
print(f"K-factor usado: {resultado['match_details']['team_a_k']:.1f}")
print(f"Expectativa: {resultado['match_details']['expected_a']:.1%}")

print("\n" + "="*80)
print("RESUMEN")
print("="*80 + "\n")

print("✅ Jugadores principiantes (0-15 partidos) con K=400:")
print("   - Victoria contra igual: ~40-50 puntos")
print("   - Victoria como underdog: ~50-70 puntos")
print("   - Derrota: ~-40 a -50 puntos")
print()
print("✅ Jugadores intermedios (16-30 partidos) con K=300:")
print("   - Cambios moderados: ~30-50 puntos")
print()
print("✅ Jugadores establecidos (31-60 partidos) con K=200:")
print("   - Cambios más estables: ~20-40 puntos")
print()
print("✅ Jugadores expertos (61+ partidos) con K=150:")
print("   - Cambios conservadores: ~15-30 puntos")

print("\n" + "="*80 + "\n")
