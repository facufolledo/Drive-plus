"""
Debug: Verificar conteo de partidos del usuario
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

USER_ID = 2  # facund10s

with engine.connect() as conn:
    print("=" * 80)
    print("🔍 DEBUG: Conteo de partidos del usuario")
    print("=" * 80)
    
    # Query actual del backend
    query_backend = text("""
        SELECT COUNT(DISTINCT p.id_partido)
        FROM partido_jugadores pj
        JOIN partidos p ON pj.id_partido = p.id_partido
        WHERE pj.id_usuario = :user_id
          AND (
            EXISTS (SELECT 1 FROM resultados_partidos WHERE id_partido = p.id_partido)
            OR EXISTS (SELECT 1 FROM historial_rating WHERE id_partido = p.id_partido AND id_usuario = :user_id)
          )
    """)
    
    result = conn.execute(query_backend, {"user_id": USER_ID}).fetchone()
    print(f"\n📊 Query del backend: {result[0]} partidos")
    
    # Verificar partidos con resultado
    query_con_resultado = text("""
        SELECT COUNT(DISTINCT p.id_partido)
        FROM partido_jugadores pj
        JOIN partidos p ON pj.id_partido = p.id_partido
        WHERE pj.id_usuario = :user_id
          AND EXISTS (SELECT 1 FROM resultados_partidos WHERE id_partido = p.id_partido)
    """)
    
    result2 = conn.execute(query_con_resultado, {"user_id": USER_ID}).fetchone()
    print(f"📊 Partidos con resultado: {result2[0]}")
    
    # Verificar partidos con historial
    query_con_historial = text("""
        SELECT COUNT(DISTINCT p.id_partido)
        FROM partido_jugadores pj
        JOIN partidos p ON pj.id_partido = p.id_partido
        WHERE pj.id_usuario = :user_id
          AND EXISTS (SELECT 1 FROM historial_rating WHERE id_partido = p.id_partido AND id_usuario = :user_id)
    """)
    
    result3 = conn.execute(query_con_historial, {"user_id": USER_ID}).fetchone()
    print(f"📊 Partidos con historial: {result3[0]}")
    
    # Listar todos los partidos del usuario
    query_lista = text("""
        SELECT DISTINCT p.id_partido, p.fecha,
               EXISTS (SELECT 1 FROM resultados_partidos WHERE id_partido = p.id_partido) as tiene_resultado,
               EXISTS (SELECT 1 FROM historial_rating WHERE id_partido = p.id_partido AND id_usuario = :user_id) as tiene_historial
        FROM partido_jugadores pj
        JOIN partidos p ON pj.id_partido = p.id_partido
        WHERE pj.id_usuario = :user_id
        ORDER BY p.fecha DESC
        LIMIT 10
    """)
    
    partidos = conn.execute(query_lista, {"user_id": USER_ID}).fetchall()
    print(f"\n📋 Últimos {len(partidos)} partidos del usuario:")
    for p in partidos:
        print(f"  - Partido {p[0]} | Fecha: {p[1]} | Resultado: {p[2]} | Historial: {p[3]}")
    
    print("\n" + "=" * 80)
