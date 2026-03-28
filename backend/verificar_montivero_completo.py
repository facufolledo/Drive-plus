"""
Script para verificar todos los puntos de Montivero (ID 43)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: Variable DATABASE_URL no encontrada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def main():
    print("=" * 80)
    print("VERIFICACIÓN COMPLETA - MONTIVERO (ID 43)")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Ver todos los registros de puntos de Montivero
        print("TODOS LOS REGISTROS DE PUNTOS:")
        print("-" * 80)
        registros = conn.execute(text("""
            SELECT 
                cpj.id,
                cpj.torneo_id,
                cpj.torneo_externo,
                t.nombre as torneo_nombre,
                COALESCE(tc.nombre, cpj.categoria_nombre) as categoria,
                cpj.fase_alcanzada,
                cpj.puntos
            FROM circuito_puntos_jugador cpj
            LEFT JOIN torneos t ON cpj.torneo_id = t.id
            LEFT JOIN torneo_categorias tc ON cpj.categoria_id = tc.id
            WHERE cpj.usuario_id = 43
            ORDER BY cpj.puntos DESC
        """)).fetchall()
        
        total = 0
        for r in registros:
            torneo_info = r.torneo_externo if r.torneo_externo else f"T{r.torneo_id} - {r.torneo_nombre}"
            print(f"  {r.categoria:10s} | {torneo_info:40s} | {r.puntos:4d} pts ({r.fase_alcanzada})")
            total += r.puntos
        
        print("-" * 80)
        print(f"TOTAL: {total} puntos")
        print()
        
        # Ver el ranking calculado por el backend
        print("=" * 80)
        print("RANKING DESDE EL BACKEND (como lo ve el frontend):")
        print("=" * 80)
        print()
        
        ranking = conn.execute(text("""
            SELECT 
                cpj.usuario_id,
                COALESCE(p.nombre || ' ' || p.apellido, u.nombre_usuario) as nombre,
                COALESCE(tc.nombre, cpj.categoria_nombre) as categoria,
                SUM(cpj.puntos) as total_puntos,
                COUNT(DISTINCT COALESCE(cpj.torneo_externo, CAST(cpj.torneo_id AS TEXT))) as torneos_jugados
            FROM circuito_puntos_jugador cpj
            JOIN usuarios u ON cpj.usuario_id = u.id_usuario
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            LEFT JOIN torneo_categorias tc ON cpj.categoria_id = tc.id
            WHERE cpj.circuito_id = 1
            GROUP BY cpj.usuario_id, u.nombre_usuario, p.nombre, p.apellido, COALESCE(tc.nombre, cpj.categoria_nombre)
            HAVING SUM(cpj.puntos) > 0
            ORDER BY total_puntos DESC
            LIMIT 10
        """)).fetchall()
        
        for i, r in enumerate(ranking, 1):
            print(f"{i:2d}. {r.nombre:40s} | {r.categoria:10s} | {r.total_puntos:5d} pts ({r.torneos_jugados} torneos)")

if __name__ == "__main__":
    main()
