#!/usr/bin/env python3
"""
Verificar estado de categorías del torneo 45 y resetear si es necesario.
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

def verificar():
    s = Session()
    try:
        print("=" * 70)
        print(f"VERIFICAR ESTADO CATEGORÍAS - TORNEO {TORNEO_ID}")
        print("=" * 70)

        # Obtener todas las categorías
        categorias = s.execute(text("""
            SELECT id, nombre, estado, 
                   (SELECT COUNT(*) FROM torneos_parejas WHERE categoria_id = tc.id AND estado = 'confirmada') as parejas,
                   (SELECT COUNT(*) FROM torneo_zonas WHERE categoria_id = tc.id) as zonas,
                   (SELECT COUNT(*) FROM partidos p 
                    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id 
                    WHERE tp1.categoria_id = tc.id AND tp1.torneo_id = :t) as partidos
            FROM torneo_categorias tc
            WHERE torneo_id = :t
            ORDER BY nombre
        """), {"t": TORNEO_ID}).fetchall()

        print(f"\n📋 Estado actual:")
        for cat in categorias:
            print(f"\n   {cat[1]}:")
            print(f"      Estado: {cat[2]}")
            print(f"      Parejas: {cat[3]}")
            print(f"      Zonas: {cat[4]}")
            print(f"      Partidos: {cat[5]}")

        # Preguntar si quiere resetear alguna categoría
        print(f"\n{'=' * 70}")
        print("Para generar fixture de otras categorías, deben estar en estado 'inscripcion'")
        print("¿Querés resetear alguna categoría a 'inscripcion'? (s/n)")
        
        # Por ahora solo mostrar info, no hacer cambios automáticos
        print("\nPara resetear manualmente una categoría, ejecutá:")
        print("UPDATE torneo_categorias SET estado = 'inscripcion' WHERE id = [ID_CATEGORIA];")
        
        print(f"\n{'=' * 70}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    verificar()
