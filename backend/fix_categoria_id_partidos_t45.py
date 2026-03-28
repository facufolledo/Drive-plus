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
        print("ACTUALIZAR categoria_id EN PARTIDOS - TORNEO 45")
        print("=" * 80)
        
        # Actualizar categoria_id desde las zonas
        result = s.execute(text("""
            UPDATE partidos p
            SET categoria_id = tz.categoria_id
            FROM torneo_zonas tz
            WHERE p.zona_id = tz.id
            AND p.id_torneo = :tid
            AND p.categoria_id IS NULL
        """), {"tid": TORNEO_ID})
        
        s.commit()
        
        print(f"\n✅ Actualizados {result.rowcount} partidos con categoria_id")
        
        # Verificar por categoría
        print("\n📊 VERIFICACIÓN POR CATEGORÍA:")
        print("─" * 80)
        
        categorias = s.execute(text("""
            SELECT 
                tc.id,
                tc.nombre,
                COUNT(p.id_partido) as total_partidos
            FROM torneo_categorias tc
            LEFT JOIN partidos p ON p.categoria_id = tc.id AND p.id_torneo = :tid
            WHERE tc.torneo_id = :tid
            GROUP BY tc.id, tc.nombre
            ORDER BY tc.nombre
        """), {"tid": TORNEO_ID}).fetchall()
        
        total = 0
        for cat in categorias:
            print(f"  {cat[1]}: {cat[2]} partidos")
            total += cat[2]
        
        print(f"\n  TOTAL: {total} partidos")
        
        # Verificar que no queden partidos sin categoria_id
        sin_categoria = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos
            WHERE id_torneo = :tid
            AND categoria_id IS NULL
        """), {"tid": TORNEO_ID}).scalar()
        
        if sin_categoria > 0:
            print(f"\n⚠️  Aún hay {sin_categoria} partidos sin categoria_id")
        else:
            print("\n✅ Todos los partidos tienen categoria_id")
        
        print("\n🎉 ¡Listo! Ahora el frontend debería listar los partidos correctamente.")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
