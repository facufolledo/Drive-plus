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
        print("SIMULAR ENDPOINT listar_partidos_torneo - TORNEO 45")
        print("=" * 80)
        
        # Simular la query del endpoint
        result = s.execute(text("""
            SELECT 
                p.id_partido,
                p.id_torneo,
                p.pareja1_id,
                p.pareja2_id,
                p.zona_id,
                tz.nombre as zona_nombre,
                tc.nombre as categoria_nombre,
                p.fecha_hora,
                p.estado
            FROM partidos p
            LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
            LEFT JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE p.id_torneo = :tid
            ORDER BY tc.nombre, tz.nombre, p.fecha_hora
        """), {"tid": TORNEO_ID}).fetchall()
        
        print(f"\n✅ El endpoint devolvería {len(result)} partidos")
        
        # Agrupar por categoría
        por_categoria = {}
        for row in result:
            cat = row[6] or "Sin categoría"
            if cat not in por_categoria:
                por_categoria[cat] = 0
            por_categoria[cat] += 1
        
        print("\n📊 Partidos por categoría:")
        print("─" * 80)
        for cat, count in sorted(por_categoria.items()):
            print(f"  {cat}: {count} partidos")
        
        # Mostrar primeros 5
        print("\n📋 Primeros 5 partidos:")
        print("─" * 80)
        for row in result[:5]:
            print(f"  Partido #{row[0]} - {row[6]} {row[5]} - {row[7]} - Estado: {row[8]}")
        
        print("\n🎉 ¡El endpoint está funcionando correctamente!")
        print("El frontend debería mostrar todos los partidos ahora.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
