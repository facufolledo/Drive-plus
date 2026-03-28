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
        print("DEBUG PARTIDOS EXTRA - TORNEO 45")
        print("=" * 80)
        
        # Ver detalle por zona
        print("\n📋 DETALLE POR ZONA:")
        zonas = s.execute(text("""
            SELECT 
                tc.nombre as categoria,
                tz.nombre as zona,
                COUNT(DISTINCT tzp.pareja_id) as parejas,
                COUNT(DISTINCT p.id_partido) as partidos
            FROM torneo_zonas tz
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            LEFT JOIN torneo_zona_parejas tzp ON tzp.zona_id = tz.id
            LEFT JOIN partidos p ON p.zona_id = tz.id
            WHERE tc.torneo_id = :tid
            GROUP BY tc.nombre, tz.nombre
            ORDER BY tc.nombre, tz.nombre
        """), {"tid": TORNEO_ID}).fetchall()
        
        print(f"{'Categoría':<10} {'Zona':<10} {'Parejas':<10} {'Partidos':<10} {'Esperado':<10}")
        print("-" * 60)
        
        for z in zonas:
            categoria, zona, parejas, partidos = z
            # Calcular partidos esperados: n parejas = n*(n-1)/2 partidos
            esperado = (parejas * (parejas - 1)) // 2 if parejas > 0 else 0
            estado = "✅" if partidos == esperado else "⚠️"
            print(f"{categoria:<10} {zona:<10} {parejas:<10} {partidos:<10} {esperado:<10} {estado}")
        
        # Buscar zonas con problemas
        print("\n🔍 ZONAS CON PARTIDOS EXTRA:")
        problemas = s.execute(text("""
            SELECT 
                tc.nombre as categoria,
                tz.nombre as zona,
                tz.id as zona_id,
                COUNT(DISTINCT tzp.pareja_id) as parejas,
                COUNT(DISTINCT p.id_partido) as partidos
            FROM torneo_zonas tz
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            LEFT JOIN torneo_zona_parejas tzp ON tzp.zona_id = tz.id
            LEFT JOIN partidos p ON p.zona_id = tz.id
            WHERE tc.torneo_id = :tid
            GROUP BY tc.nombre, tz.nombre, tz.id
            HAVING COUNT(DISTINCT p.id_partido) > (COUNT(DISTINCT tzp.pareja_id) * (COUNT(DISTINCT tzp.pareja_id) - 1)) / 2
        """), {"tid": TORNEO_ID}).fetchall()
        
        if problemas:
            for p in problemas:
                print(f"\n⚠️  {p[0]} - {p[1]} (ID: {p[2]})")
                print(f"   Parejas: {p[3]}, Partidos: {p[4]}, Esperado: {(p[3] * (p[3] - 1)) // 2}")
                
                # Ver partidos de esta zona
                partidos = s.execute(text("""
                    SELECT 
                        p.id_partido,
                        p.pareja1_id,
                        p.pareja2_id,
                        p.fecha_hora,
                        p.cancha_id
                    FROM partidos p
                    WHERE p.zona_id = :zid
                    ORDER BY p.fecha_hora
                """), {"zid": p[2]}).fetchall()
                
                print(f"\n   Partidos en esta zona:")
                for partido in partidos:
                    print(f"   - ID {partido[0]}: Pareja {partido[1]} vs {partido[2]} | {partido[3]} | Cancha {partido[4]}")
        else:
            print("✅ No hay zonas con partidos extra")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
