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
        print("VERIFICAR FIXTURE COMPLETO - TORNEO 45")
        print("=" * 80)
        
        # Contar por categoría
        categorias = s.execute(text("""
            SELECT 
                tc.nombre,
                COUNT(DISTINCT tz.id) as zonas,
                COUNT(DISTINCT tp.id) as parejas,
                COUNT(DISTINCT p.id_partido) as partidos
            FROM torneo_categorias tc
            LEFT JOIN torneo_zonas tz ON tz.categoria_id = tc.id
            LEFT JOIN torneo_zona_parejas tzp ON tzp.zona_id = tz.id
            LEFT JOIN torneos_parejas tp ON tp.id = tzp.pareja_id
            LEFT JOIN partidos p ON p.zona_id = tz.id AND p.id_torneo = :tid
            WHERE tc.torneo_id = :tid
            GROUP BY tc.nombre
            ORDER BY tc.nombre
        """), {"tid": TORNEO_ID}).fetchall()
        
        print("\n📊 RESUMEN POR CATEGORÍA:")
        print("-" * 80)
        print(f"{'Categoría':<15} {'Zonas':<10} {'Parejas':<10} {'Partidos':<10}")
        print("-" * 80)
        
        total_zonas = 0
        total_parejas = 0
        total_partidos = 0
        
        for cat in categorias:
            print(f"{cat[0]:<15} {cat[1]:<10} {cat[2]:<10} {cat[3]:<10}")
            total_zonas += cat[1]
            total_parejas += cat[2]
            total_partidos += cat[3]
        
        print("-" * 80)
        print(f"{'TOTAL':<15} {total_zonas:<10} {total_parejas:<10} {total_partidos:<10}")
        
        # Verificar que todos los partidos tengan id_torneo y categoria_id
        print("\n🔍 VERIFICAR CAMPOS REQUERIDOS:")
        partidos_sin_id_torneo = s.execute(text("""
            SELECT COUNT(*) FROM partidos p
            JOIN torneo_zonas tz ON p.zona_id = tz.id
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = :tid AND p.id_torneo IS NULL
        """), {"tid": TORNEO_ID}).scalar()
        
        partidos_sin_categoria = s.execute(text("""
            SELECT COUNT(*) FROM partidos p
            JOIN torneo_zonas tz ON p.zona_id = tz.id
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = :tid AND p.categoria_id IS NULL
        """), {"tid": TORNEO_ID}).scalar()
        
        if partidos_sin_id_torneo == 0 and partidos_sin_categoria == 0:
            print("✅ Todos los partidos tienen id_torneo y categoria_id")
        else:
            print(f"⚠️  Partidos sin id_torneo: {partidos_sin_id_torneo}")
            print(f"⚠️  Partidos sin categoria_id: {partidos_sin_categoria}")
        
        # Verificar distribución por día
        print("\n📅 DISTRIBUCIÓN POR DÍA:")
        dias = s.execute(text("""
            SELECT 
                fecha,
                COUNT(*) as partidos
            FROM partidos
            WHERE id_torneo = :tid
            GROUP BY fecha
            ORDER BY fecha
        """), {"tid": TORNEO_ID}).fetchall()
        
        for dia in dias:
            print(f"  {dia[0]}: {dia[1]} partidos")
        
        # Verificar distribución por cancha
        print("\n🏟 DISTRIBUCIÓN POR CANCHA:")
        canchas = s.execute(text("""
            SELECT 
                cancha_id,
                COUNT(*) as partidos
            FROM partidos
            WHERE id_torneo = :tid
            GROUP BY cancha_id
            ORDER BY cancha_id
        """), {"tid": TORNEO_ID}).fetchall()
        
        for cancha in canchas:
            print(f"  Cancha {cancha[0]}: {cancha[1]} partidos")
        
        print("\n" + "=" * 80)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("=" * 80)
        print(f"\nTOTAL ESPERADO: 68 partidos (18 de 8va + 28 de 6ta + 22 de 4ta)")
        print(f"TOTAL CREADO: {total_partidos} partidos")
        
        if total_partidos == 68:
            print("\n🎉 ¡FIXTURE COMPLETO CREADO CORRECTAMENTE!")
        else:
            print(f"\n⚠️  Faltan {68 - total_partidos} partidos")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
