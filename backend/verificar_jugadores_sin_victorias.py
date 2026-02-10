"""
Verificar jugadores que tienen partidos pero 0 victorias
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv('backend/.env')

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

print("=" * 60)
print("VERIFICANDO JUGADORES SIN VICTORIAS")
print("=" * 60)

jugadores_problema = [200, 209, 50, 210, 57]  # IDs de los jugadores con problema

with engine.connect() as conn:
    for user_id in jugadores_problema:
        print(f"\n{'=' * 60}")
        
        # Obtener info del usuario
        result = conn.execute(text("""
            SELECT nombre_usuario, rating, partidos_jugados
            FROM usuarios
            WHERE id_usuario = :user_id
        """), {"user_id": user_id})
        
        user = result.fetchone()
        if not user:
            print(f"Usuario {user_id} no encontrado")
            continue
        
        print(f"Usuario: {user[0]} (ID: {user_id})")
        print(f"Rating: {user[1]} | Partidos jugados (campo): {user[2]}")
        
        # Obtener historial de rating
        result = conn.execute(text("""
            SELECT 
                hr.id_partido,
                hr.delta,
                hr.rating_antes,
                hr.rating_despues,
                p.estado
            FROM historial_rating hr
            JOIN partidos p ON hr.id_partido = p.id_partido
            WHERE hr.id_usuario = :user_id
            ORDER BY hr.creado_en DESC
        """), {"user_id": user_id})
        
        print("\nHistorial de partidos:")
        print("-" * 60)
        
        victorias = 0
        derrotas = 0
        
        for row in result:
            id_partido, delta, rating_ant, rating_nuevo, estado = row
            resultado = "VICTORIA" if delta > 0 else "DERROTA" if delta < 0 else "EMPATE"
            
            if delta > 0:
                victorias += 1
            elif delta < 0:
                derrotas += 1
            
            print(f"Partido {id_partido}: {resultado} | Delta: {delta:+d} | {rating_ant} → {rating_nuevo} | Estado: {estado}")
        
        print(f"\nResumen: {victorias} victorias, {derrotas} derrotas")
        
        if victorias == 0 and derrotas > 0:
            print("✅ CORRECTO: Este jugador perdió todos sus partidos, por eso 0 victorias")
        elif victorias > 0:
            print("❌ ERROR: Tiene victorias en BD pero el endpoint devuelve 0")

print("\n" + "=" * 60)
print("CONCLUSIÓN")
print("=" * 60)
print("\nSi todos los jugadores con 0 victorias efectivamente perdieron")
print("todos sus partidos, entonces el endpoint está funcionando CORRECTAMENTE.")
