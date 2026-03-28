"""
Script para verificar los puntos insertados del torneo externo ZF
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
    print("VERIFICACIÓN DE PUNTOS INSERTADOS")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Ver todos los registros del torneo externo
        registros = conn.execute(text("""
            SELECT 
                cpj.id,
                cpj.circuito_id,
                cpj.torneo_id,
                cpj.torneo_externo,
                cpj.categoria_id,
                cpj.categoria_nombre,
                cpj.usuario_id,
                u.nombre_usuario,
                COALESCE(pu.nombre || ' ' || pu.apellido, u.nombre_usuario) as nombre_completo,
                cpj.fase_alcanzada,
                cpj.puntos
            FROM circuito_puntos_jugador cpj
            JOIN usuarios u ON cpj.usuario_id = u.id_usuario
            LEFT JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE cpj.torneo_externo = 'ZF-7MA-MAR2026'
            ORDER BY cpj.puntos DESC, nombre_completo
        """)).fetchall()
        
        print(f"Total de registros encontrados: {len(registros)}")
        print()
        
        if registros:
            print("Registros insertados:")
            print("-" * 80)
            for r in registros:
                print(f"ID: {r.id:3d} | Usuario: {r.usuario_id:3d} - {r.nombre_completo:30s} | {r.puntos:4d} pts ({r.fase_alcanzada})")
        else:
            print("⚠️  No se encontraron registros")
        
        print()
        print("=" * 80)
        print("RANKING COMPLETO 7MA (incluyendo torneos externos)")
        print("=" * 80)
        print()
        
        # Ranking que incluye torneos externos
        ranking = conn.execute(text("""
            SELECT 
                u.id_usuario,
                COALESCE(pu.nombre || ' ' || pu.apellido, u.nombre_usuario) as nombre,
                SUM(cpj.puntos) as total_puntos,
                COUNT(*) as torneos_jugados,
                STRING_AGG(
                    COALESCE(cpj.torneo_externo, 'T' || cpj.torneo_id::TEXT), 
                    ', ' ORDER BY cpj.puntos DESC
                ) as torneos
            FROM circuito_puntos_jugador cpj
            JOIN usuarios u ON cpj.usuario_id = u.id_usuario
            LEFT JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE cpj.circuito_id = 1
              AND (cpj.categoria_nombre = '7ma' OR cpj.categoria_id IN (
                  SELECT id_categoria FROM categorias WHERE nombre = '7ma'
              ))
            GROUP BY u.id_usuario, pu.nombre, pu.apellido, u.nombre_usuario
            ORDER BY total_puntos DESC
            LIMIT 20
        """)).fetchall()
        
        for i, row in enumerate(ranking, 1):
            print(f"{i:2d}. {row.nombre:40s} - {row.total_puntos:5d} pts ({row.torneos_jugados} torneos)")
            print(f"    Torneos: {row.torneos}")
        
        print()

if __name__ == "__main__":
    main()
