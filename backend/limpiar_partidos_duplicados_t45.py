import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def main():
    s = Session()
    try:
        print("=" * 80)
        print("LIMPIAR PARTIDOS DUPLICADOS - TORNEO 45")
        print("=" * 80)
        
        # Encontrar partidos duplicados (mismo cruce en la misma zona)
        duplicados = s.execute(text("""
            WITH partidos_numerados AS (
                SELECT 
                    p.id_partido,
                    p.zona_id,
                    p.pareja1_id,
                    p.pareja2_id,
                    p.fecha_hora,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.zona_id, 
                        LEAST(p.pareja1_id, p.pareja2_id),
                        GREATEST(p.pareja1_id, p.pareja2_id)
                        ORDER BY p.id_partido
                    ) as rn
                FROM partidos p
                JOIN torneos_parejas tp ON p.pareja1_id = tp.id
                WHERE tp.torneo_id = :tid
            )
            SELECT id_partido, zona_id, pareja1_id, pareja2_id
            FROM partidos_numerados
            WHERE rn > 1
            ORDER BY zona_id, id_partido
        """), {"tid": TORNEO_ID}).fetchall()
        
        if not duplicados:
            print("\n✅ No hay partidos duplicados")
            
            # Mostrar totales
            total_partidos = s.execute(text("""
                SELECT COUNT(*)
                FROM partidos p
                JOIN torneos_parejas tp ON p.pareja1_id = tp.id
                WHERE tp.torneo_id = :tid
            """), {"tid": TORNEO_ID}).scalar()
            
            print(f"Total partidos: {total_partidos}")
            return
        
        print(f"\n⚠️  Encontrados {len(duplicados)} partidos duplicados:")
        
        for dup in duplicados:
            print(f"  Partido #{dup[0]} - Zona {dup[1]} - Parejas {dup[2]} vs {dup[3]}")
        
        # Eliminar duplicados
        ids_a_eliminar = [d[0] for d in duplicados]
        
        result = s.execute(text("""
            DELETE FROM partidos
            WHERE id_partido = ANY(:ids)
        """), {"ids": ids_a_eliminar})
        
        s.commit()
        
        print(f"\n✅ Eliminados {result.rowcount} partidos duplicados")
        
        # Verificar totales finales
        total_partidos = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp ON p.pareja1_id = tp.id
            WHERE tp.torneo_id = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        total_parejas = s.execute(text("""
            SELECT COUNT(*)
            FROM torneos_parejas
            WHERE torneo_id = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        print(f"\n{'=' * 80}")
        print("TOTALES FINALES")
        print("=" * 80)
        print(f"  Total parejas: {total_parejas} (esperado: 68)")
        print(f"  Total partidos: {total_partidos} (esperado: 65)")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
