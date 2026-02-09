"""
Ver partidos de principiantes en torneo 37
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Ver partidos de principiantes en torneo 37
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
            u1.nombre_usuario as j1_username,
            u2.nombre_usuario as j2_username,
            u3.nombre_usuario as j3_username,
            u4.nombre_usuario as j4_username,
            u1.rating as j1_rating,
            u2.rating as j2_rating,
            u3.rating as j3_rating,
            u4.rating as j4_rating,
            pu1.nombre as j1_nombre,
            pu1.apellido as j1_apellido,
            pu2.nombre as j2_nombre,
            pu2.apellido as j2_apellido,
            pu3.nombre as j3_nombre,
            pu3.apellido as j3_apellido,
            pu4.nombre as j4_nombre,
            pu4.apellido as j4_apellido
        FROM partidos p
        INNER JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        INNER JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        INNER JOIN usuarios u1 ON tp1.jugador1_id = u1.id_usuario
        INNER JOIN usuarios u2 ON tp1.jugador2_id = u2.id_usuario
        INNER JOIN usuarios u3 ON tp2.jugador1_id = u3.id_usuario
        INNER JOIN usuarios u4 ON tp2.jugador2_id = u4.id_usuario
        INNER JOIN perfil_usuarios pu1 ON u1.id_usuario = pu1.id_usuario
        INNER JOIN perfil_usuarios pu2 ON u2.id_usuario = pu2.id_usuario
        INNER JOIN perfil_usuarios pu3 ON u3.id_usuario = pu3.id_usuario
        INNER JOIN perfil_usuarios pu4 ON u4.id_usuario = pu4.id_usuario
        WHERE p.id_torneo = 37
          AND tp1.categoria_id = 84
          AND p.estado = 'confirmado'
        ORDER BY p.id_partido
    """)
    
    result = conn.execute(query)
    partidos = result.fetchall()
    
    print(f"\n{'='*120}")
    print(f"PARTIDOS DE PRINCIPIANTES EN TORNEO 37")
    print(f"{'='*120}\n")
    
    for partido in partidos:
        print(f"Partido {partido.id_partido}:")
        print(f"  Pareja 1 (ID {partido.pareja1_id}): {partido.j1_nombre} {partido.j1_apellido} ({partido.j1_rating}) + {partido.j2_nombre} {partido.j2_apellido} ({partido.j2_rating})")
        print(f"  Pareja 2 (ID {partido.pareja2_id}): {partido.j3_nombre} {partido.j3_apellido} ({partido.j3_rating}) + {partido.j4_nombre} {partido.j4_apellido} ({partido.j4_rating})")
        print(f"  Resultado: {partido.resultado_padel}")
        print(f"  Ganador: Pareja {partido.ganador_pareja_id}")
        print()
