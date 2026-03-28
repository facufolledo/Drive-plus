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
        print("LIMPIAR COMPLETAMENTE TORNEO 45")
        print("=" * 80)
        
        # 1. Eliminar todos los partidos
        print("\n1️⃣ Eliminando partidos...")
        result = s.execute(text("""
            DELETE FROM partidos
            WHERE id_torneo = :tid
        """), {"tid": TORNEO_ID})
        print(f"✅ Eliminados {result.rowcount} partidos")
        
        # 2. Eliminar relaciones zona-pareja
        print("\n2️⃣ Eliminando relaciones zona-pareja...")
        result = s.execute(text("""
            DELETE FROM torneo_zona_parejas
            WHERE zona_id IN (
                SELECT tz.id
                FROM torneo_zonas tz
                JOIN torneo_categorias tc ON tz.categoria_id = tc.id
                WHERE tc.torneo_id = :tid
            )
        """), {"tid": TORNEO_ID})
        print(f"✅ Eliminadas {result.rowcount} relaciones")
        
        # 3. Eliminar parejas
        print("\n3️⃣ Eliminando parejas...")
        result = s.execute(text("""
            DELETE FROM torneos_parejas
            WHERE torneo_id = :tid
        """), {"tid": TORNEO_ID})
        print(f"✅ Eliminadas {result.rowcount} parejas")
        
        # 4. Eliminar zonas
        print("\n4️⃣ Eliminando zonas...")
        result = s.execute(text("""
            DELETE FROM torneo_zonas
            WHERE categoria_id IN (
                SELECT id FROM torneo_categorias WHERE torneo_id = :tid
            )
        """), {"tid": TORNEO_ID})
        print(f"✅ Eliminadas {result.rowcount} zonas")
        
        s.commit()
        
        print("\n🎉 Torneo 45 limpiado completamente")
        print("Ahora puedes recrear todo desde cero con los datos correctos")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
