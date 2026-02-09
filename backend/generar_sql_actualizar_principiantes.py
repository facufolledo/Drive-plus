"""
Generar SQL para actualizar ratings de principiantes con nuevos K-factors
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.services.elo_service import EloService

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
elo_service = EloService()

# Obtener partidos de principiantes
with engine.connect() as conn:
    query = text("""
        SELECT 
            p.id_partido,
            p.ganador_pareja_id,
            p.resultado_padel,
            tp1.id as pareja1_id,
            tp1.jugador1_id as p1_j1,
            tp1.jugador2_id as p1_j2,
            tp2.id as pareja2_id,
            tp2.jugador1_id as p2_j1,
            tp2.jugador2_id as p2_j2,
            u1.rating as j1_rating,
            u2.rating as j2_rating,
            u3.rating as j3_rating,
            u4.rating as j4_rating
        FROM partidos p
        INNER JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        INNER JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        INNER JOIN usuarios u1 ON tp1.jugador1_id = u1.id_usuario
        INNER JOIN usuarios u2 ON tp1.jugador2_id = u2.id_usuario
        INNER JOIN usuarios u3 ON tp2.jugador1_id = u3.id_usuario
        INNER JOIN usuarios u4 ON tp2.jugador2_id = u4.id_usuario
        WHERE p.id_torneo = 37
          AND tp1.categoria_id = 84
          AND p.estado = 'confirmado'
        ORDER BY p.id_partido
    """)
    
    partidos = conn.execute(query).fetchall()

# Diccionario para trackear ratings de cada jugador
ratings_jugadores = {}
cambios_por_jugador = {}

print("-- SQL para actualizar ratings de principiantes con K=400")
print("-- Generado automáticamente\n")

for partido in partidos:
    # Parsear resultado
    resultado = json.loads(partido.resultado_padel) if isinstance(partido.resultado_padel, str) else partido.resultado_padel
    sets = resultado.get('sets', [])
    
    # Calcular sets y games
    sets_a = sum(1 for s in sets if s.get('ganador') == 'equipoA')
    sets_b = sum(1 for s in sets if s.get('ganador') == 'equipoB')
    games_a = sum(s.get('gamesEquipoA', 0) for s in sets)
    games_b = sum(s.get('gamesEquipoB', 0) for s in sets)
    
    # IDs de jugadores
    j1_id, j2_id, j3_id, j4_id = partido.p1_j1, partido.p1_j2, partido.p2_j1, partido.p2_j2
    
    # Obtener ratings actuales (o iniciales si es su primer partido)
    r1 = ratings_jugadores.get(j1_id, partido.j1_rating)
    r2 = ratings_jugadores.get(j2_id, partido.j2_rating)
    r3 = ratings_jugadores.get(j3_id, partido.j3_rating)
    r4 = ratings_jugadores.get(j4_id, partido.j4_rating)
    
    # Inicializar contadores de partidos
    if j1_id not in cambios_por_jugador:
        cambios_por_jugador[j1_id] = []
    if j2_id not in cambios_por_jugador:
        cambios_por_jugador[j2_id] = []
    if j3_id not in cambios_por_jugador:
        cambios_por_jugador[j3_id] = []
    if j4_id not in cambios_por_jugador:
        cambios_por_jugador[j4_id] = []
    
    partidos_j1 = len(cambios_por_jugador[j1_id])
    partidos_j2 = len(cambios_por_jugador[j2_id])
    partidos_j3 = len(cambios_por_jugador[j3_id])
    partidos_j4 = len(cambios_por_jugador[j4_id])
    
    # Calcular ELO con nuevos K-factors
    team_a = [
        {"rating": r1, "partidos": partidos_j1, "volatilidad": 1.0, "id": j1_id},
        {"rating": r2, "partidos": partidos_j2, "volatilidad": 1.0, "id": j2_id}
    ]
    
    team_b = [
        {"rating": r3, "partidos": partidos_j3, "volatilidad": 1.0, "id": j3_id},
        {"rating": r4, "partidos": partidos_j4, "volatilidad": 1.0, "id": j4_id}
    ]
    
    resultado_elo = elo_service.calculate_match_ratings(
        team_a_players=team_a,
        team_b_players=team_b,
        sets_a=sets_a,
        sets_b=sets_b,
        games_a=games_a,
        games_b=games_b,
        match_type="zona"
    )
    
    # Nuevos ratings
    nuevo_r1 = resultado_elo["team_a"]["players"][0]["new_rating"]
    nuevo_r2 = resultado_elo["team_a"]["players"][1]["new_rating"]
    nuevo_r3 = resultado_elo["team_b"]["players"][0]["new_rating"]
    nuevo_r4 = resultado_elo["team_b"]["players"][1]["new_rating"]
    
    # Deltas
    delta1 = resultado_elo["team_a"]["players"][0]["rating_change"]
    delta2 = resultado_elo["team_a"]["players"][1]["rating_change"]
    delta3 = resultado_elo["team_b"]["players"][0]["rating_change"]
    delta4 = resultado_elo["team_b"]["players"][1]["rating_change"]
    
    # Actualizar ratings en memoria
    ratings_jugadores[j1_id] = nuevo_r1
    ratings_jugadores[j2_id] = nuevo_r2
    ratings_jugadores[j3_id] = nuevo_r3
    ratings_jugadores[j4_id] = nuevo_r4
    
    # Guardar cambios
    cambios_por_jugador[j1_id].append((partido.id_partido, r1, delta1, nuevo_r1))
    cambios_por_jugador[j2_id].append((partido.id_partido, r2, delta2, nuevo_r2))
    cambios_por_jugador[j3_id].append((partido.id_partido, r3, delta3, nuevo_r3))
    cambios_por_jugador[j4_id].append((partido.id_partido, r4, delta4, nuevo_r4))

# Generar SQL
import sys
sys.stdout.reconfigure(encoding='utf-8')
print("BEGIN;\n")

# Actualizar historial_rating
print("-- Actualizar historial_rating")
for jugador_id, cambios in cambios_por_jugador.items():
    for partido_id, rating_antes, delta, rating_despues in cambios:
        print(f"UPDATE historial_rating SET rating_antes = {rating_antes}, delta = {delta:.1f}, rating_despues = {rating_despues} WHERE id_usuario = {jugador_id} AND id_partido = {partido_id};")

print("\n-- Actualizar rating actual de usuarios")
for jugador_id, rating_final in ratings_jugadores.items():
    print(f"UPDATE usuarios SET rating = {rating_final} WHERE id_usuario = {jugador_id};")

print("\nCOMMIT;")

# Resumen
print(f"\n-- Resumen:")
print(f"-- Jugadores actualizados: {len(ratings_jugadores)}")
print(f"-- Partidos procesados: {len(partidos)}")
