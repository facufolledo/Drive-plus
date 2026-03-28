import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

# Configuración de parejas por zona
PAREJAS_POR_ZONA = {
    '6ta': {'A': 3, 'B': 3, 'C': 3, 'D': 3, 'E': 3, 'F': 3, 'G': 3, 'H': 3, 'I': 3},
    '4ta': {'A': 3, 'B': 3, 'C': 3, 'D': 3, 'E': 3, 'F': 3, 'G': 2, 'H': 2, 'I': 2},
    '8va': {'A': 3, 'B': 3, 'C': 3, 'D': 3, 'E': 3, 'F': 2, 'G': 2}
}

def main():
    s = Session()
    try:
        print("=" * 80)
        print("LIMPIAR DUPLICADOS - TORNEO 45")
        print("=" * 80)
        
        total_parejas_eliminadas = 0
        total_partidos_eliminados = 0
        
        for cat_nombre, zonas in PAREJAS_POR_ZONA.items():
            print(f"\n📂 {cat_nombre}")
            
            for zona_nombre, max_parejas in zonas.items():
                # Buscar zona
                zona = s.execute(text("""
                    SELECT tz.id
                    FROM torneo_zonas tz
                    JOIN torneo_categorias tc ON tz.categoria_id = tc.id
                    WHERE tc.torneo_id = :tid
                    AND tc.nombre = :cat
                    AND tz.nombre = :zona
                """), {
                    "tid": TORNEO_ID,
                    "cat": cat_nombre,
                    "zona": f"Zona {zona_nombre}"
                }).fetchone()
                
                if not zona:
                    continue
                
                # Obtener todas las parejas de la zona ordenadas por ID
                parejas = s.execute(text("""
                    SELECT tp.id
                    FROM torneos_parejas tp
                    JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
                    WHERE tzp.zona_id = :zid
                    ORDER BY tp.id
                """), {"zid": zona.id}).fetchall()
                
                if len(parejas) <= max_parejas:
                    print(f"  Zona {zona_nombre}: {len(parejas)}/{max_parejas} ✅")
                    continue
                
                # Identificar parejas a eliminar (las que sobran)
                parejas_a_mantener = [p[0] for p in parejas[:max_parejas]]
                parejas_a_eliminar = [p[0] for p in parejas[max_parejas:]]
                
                print(f"  Zona {zona_nombre}: {len(parejas)}/{max_parejas} ⚠️")
                print(f"    Manteniendo: {parejas_a_mantener}")
                print(f"    Eliminando: {parejas_a_eliminar}")
                
                # Eliminar partidos de las parejas duplicadas
                for pareja_id in parejas_a_eliminar:
                    partidos = s.execute(text("""
                        DELETE FROM partidos
                        WHERE pareja1_id = :pid OR pareja2_id = :pid
                        RETURNING id_partido
                    """), {"pid": pareja_id}).fetchall()
                    
                    if partidos:
                        print(f"      Eliminados {len(partidos)} partidos de pareja {pareja_id}")
                        total_partidos_eliminados += len(partidos)
                
                # Eliminar relación zona-pareja
                s.execute(text("""
                    DELETE FROM torneo_zona_parejas
                    WHERE pareja_id = ANY(:pids)
                """), {"pids": parejas_a_eliminar})
                
                # Eliminar parejas
                s.execute(text("""
                    DELETE FROM torneos_parejas
                    WHERE id = ANY(:pids)
                """), {"pids": parejas_a_eliminar})
                
                total_parejas_eliminadas += len(parejas_a_eliminar)
                print(f"    ✅ Eliminadas {len(parejas_a_eliminar)} parejas duplicadas")
        
        s.commit()
        
        # Verificar totales finales
        total_parejas = s.execute(text("""
            SELECT COUNT(*)
            FROM torneos_parejas
            WHERE torneo_id = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        total_partidos = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp ON p.pareja1_id = tp.id
            WHERE tp.torneo_id = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        print(f"\n{'=' * 80}")
        print("✅ LIMPIEZA COMPLETADA")
        print("=" * 80)
        print(f"  Parejas eliminadas: {total_parejas_eliminadas}")
        print(f"  Partidos eliminados: {total_partidos_eliminados}")
        print(f"\n  Total parejas final: {total_parejas} (esperado: 68)")
        print(f"  Total partidos final: {total_partidos} (esperado: 65)")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
