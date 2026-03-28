#!/usr/bin/env python3
"""
Listar todas las parejas actuales del T45 organizadas por categoría y zona
Para poder mapear con las imágenes
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def main():
    s = Session()
    try:
        print("=" * 100)
        print("PAREJAS ACTUALES - TORNEO 45")
        print("=" * 100)
        
        # Obtener todas las parejas organizadas
        parejas = s.execute(text("""
            SELECT 
                tc.nombre as categoria,
                tz.nombre as zona,
                tp.id as pareja_id,
                tp.nombre_pareja,
                u1.nombre_usuario as j1_user,
                u2.nombre_usuario as j2_user,
                u1.nombre || ' ' || u1.apellido as j1_nombre,
                u2.nombre || ' ' || u2.apellido as j2_nombre
            FROM torneos_parejas tp
            JOIN torneo_categorias tc ON tp.categoria_id = tc.id
            LEFT JOIN torneo_zonas tz ON tp.zona_id = tz.id
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            WHERE tp.torneo_id = :tid
            ORDER BY 
                CASE tc.nombre
                    WHEN '3ra' THEN 1
                    WHEN '4ta' THEN 2
                    WHEN '5ta' THEN 3
                    WHEN '6ta' THEN 4
                    WHEN '7ma' THEN 5
                    WHEN '8va' THEN 6
                    ELSE 99
                END,
                tz.nombre,
                tp.nombre_pareja
        """), {"tid": TORNEO_ID}).fetchall()
        
        cat_actual = None
        zona_actual = None
        contador_zona = 0
        
        for p in parejas:
            if p.categoria != cat_actual:
                cat_actual = p.categoria
                zona_actual = None
                print(f"\n{'=' * 100}")
                print(f"CATEGORÍA: {cat_actual.upper()}")
                print(f"{'=' * 100}")
            
            if p.zona != zona_actual:
                zona_actual = p.zona
                contador_zona = 0
                print(f"\n  Zona {zona_actual}:")
                print(f"  {'-' * 96}")
            
            contador_zona += 1
            print(f"    {contador_zona}. [{p.pareja_id:3d}] {p.nombre_pareja:45s} | {p.j1_nombre:25s} - {p.j2_nombre:25s}")
        
        # Contar totales
        print(f"\n{'=' * 100}")
        print("RESUMEN:")
        print(f"{'=' * 100}")
        
        resumen = s.execute(text("""
            SELECT 
                tc.nombre as categoria,
                COUNT(*) as total_parejas
            FROM torneos_parejas tp
            JOIN torneo_categorias tc ON tp.categoria_id = tc.id
            WHERE tp.torneo_id = :tid
            GROUP BY tc.nombre
            ORDER BY 
                CASE tc.nombre
                    WHEN '3ra' THEN 1
                    WHEN '4ta' THEN 2
                    WHEN '5ta' THEN 3
                    WHEN '6ta' THEN 4
                    WHEN '7ma' THEN 5
                    WHEN '8va' THEN 6
                    ELSE 99
                END
        """), {"tid": TORNEO_ID}).fetchall()
        
        for r in resumen:
            print(f"  {r.categoria}: {r.total_parejas} parejas")
        
        total = sum(r.total_parejas for r in resumen)
        print(f"\n  TOTAL: {total} parejas")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
