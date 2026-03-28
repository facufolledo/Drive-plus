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
        print("VERIFICAR CAMPO id_torneo EN PARTIDOS - TORNEO 45")
        print("=" * 80)
        
        # Verificar si los partidos tienen id_torneo
        result = s.execute(text("""
            SELECT 
                p.id_partido,
                p.id_torneo,
                p.zona_id,
                tz.nombre as zona_nombre,
                tc.nombre as categoria_nombre
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
            LEFT JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tp1.torneo_id = :tid
            ORDER BY p.id_partido
            LIMIT 10
        """), {"tid": TORNEO_ID}).fetchall()
        
        print(f"\n📊 Primeros 10 partidos del torneo {TORNEO_ID}:")
        print("─" * 80)
        
        sin_id_torneo = 0
        con_id_torneo = 0
        
        for row in result:
            id_partido, id_torneo, zona_id, zona_nombre, categoria_nombre = row
            if id_torneo is None:
                sin_id_torneo += 1
                print(f"❌ Partido #{id_partido} - id_torneo: NULL - Zona: {zona_nombre} ({categoria_nombre})")
            else:
                con_id_torneo += 1
                print(f"✅ Partido #{id_partido} - id_torneo: {id_torneo} - Zona: {zona_nombre} ({categoria_nombre})")
        
        # Contar totales
        total_sin_id = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            WHERE tp1.torneo_id = :tid
            AND p.id_torneo IS NULL
        """), {"tid": TORNEO_ID}).scalar()
        
        total_con_id = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            WHERE tp1.torneo_id = :tid
            AND p.id_torneo IS NOT NULL
        """), {"tid": TORNEO_ID}).scalar()
        
        print("\n📈 TOTALES:")
        print("─" * 80)
        print(f"Partidos SIN id_torneo: {total_sin_id}")
        print(f"Partidos CON id_torneo: {total_con_id}")
        print(f"Total: {total_sin_id + total_con_id}")
        
        if total_sin_id > 0:
            print("\n⚠️  PROBLEMA DETECTADO:")
            print("Los partidos no tienen el campo id_torneo establecido.")
            print("El endpoint del frontend filtra por id_torneo, por eso no los ve.")
            print("\n💡 SOLUCIÓN:")
            print("Actualizar todos los partidos para que tengan id_torneo = 45")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
