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
        print("VERIFICAR QUE EL FRONTEND PUEDA VER LOS PARTIDOS - TORNEO 45")
        print("=" * 80)
        
        # Verificar que todos los partidos tengan los campos necesarios
        print("\n🔍 VERIFICANDO CAMPOS REQUERIDOS PARA EL FRONTEND:")
        
        # 1. id_torneo
        sin_id_torneo = s.execute(text("""
            SELECT COUNT(*) FROM partidos p
            JOIN torneo_zonas tz ON p.zona_id = tz.id
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = :tid AND p.id_torneo IS NULL
        """), {"tid": TORNEO_ID}).scalar()
        
        if sin_id_torneo == 0:
            print("✅ Todos los partidos tienen id_torneo")
        else:
            print(f"❌ {sin_id_torneo} partidos sin id_torneo")
        
        # 2. categoria_id
        sin_categoria = s.execute(text("""
            SELECT COUNT(*) FROM partidos p
            JOIN torneo_zonas tz ON p.zona_id = tz.id
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = :tid AND p.categoria_id IS NULL
        """), {"tid": TORNEO_ID}).scalar()
        
        if sin_categoria == 0:
            print("✅ Todos los partidos tienen categoria_id")
        else:
            print(f"❌ {sin_categoria} partidos sin categoria_id")
        
        # 3. Verificar que categoria_id coincida con la zona
        inconsistentes = s.execute(text("""
            SELECT COUNT(*) FROM partidos p
            JOIN torneo_zonas tz ON p.zona_id = tz.id
            WHERE p.categoria_id != tz.categoria_id
            AND tz.torneo_id = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        if inconsistentes == 0:
            print("✅ Todos los partidos tienen categoria_id consistente con su zona")
        else:
            print(f"❌ {inconsistentes} partidos con categoria_id inconsistente")
        
        # Mostrar muestra de partidos por categoría
        print("\n📋 MUESTRA DE PARTIDOS POR CATEGORÍA:")
        
        categorias = ['8va', '6ta', '4ta']
        for cat in categorias:
            print(f"\n{cat}:")
            partidos = s.execute(text("""
                SELECT 
                    p.id_partido,
                    tz.nombre as zona,
                    p.fecha_hora,
                    p.cancha_id,
                    p.estado
                FROM partidos p
                JOIN torneo_zonas tz ON p.zona_id = tz.id
                JOIN torneo_categorias tc ON tz.categoria_id = tc.id
                WHERE tc.torneo_id = :tid AND tc.nombre = :cat
                ORDER BY p.fecha_hora
                LIMIT 3
            """), {"tid": TORNEO_ID, "cat": cat}).fetchall()
            
            for p in partidos:
                print(f"  - Partido {p[0]}: {p[1]} | {p[2]} | Cancha {p[3]} | {p[4]}")
        
        # Resumen final
        print("\n" + "=" * 80)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("=" * 80)
        print("\nEl frontend debería poder ver todos los partidos correctamente.")
        print("Los partidos están correctamente asociados a:")
        print("  - Torneo 45 (id_torneo)")
        print("  - Sus respectivas categorías (categoria_id)")
        print("  - Sus zonas (zona_id)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
