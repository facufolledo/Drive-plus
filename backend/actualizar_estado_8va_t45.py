#!/usr/bin/env python3
"""
Actualizar estado de 8va a 'fase_grupos' ya que tiene partidos generados.
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

def actualizar():
    s = Session()
    try:
        print("=" * 70)
        print(f"ACTUALIZAR ESTADO 8VA - TORNEO {TORNEO_ID}")
        print("=" * 70)

        # Obtener ID de 8va
        cat = s.execute(text("""
            SELECT id, estado FROM torneo_categorias 
            WHERE torneo_id = :t AND nombre = '8va'
        """), {"t": TORNEO_ID}).fetchone()

        if not cat:
            print("\n❌ Categoría 8va no encontrada")
            return

        cat_id = cat[0]
        estado_actual = cat[1]

        print(f"\n✅ Categoría 8va (ID: {cat_id})")
        print(f"   Estado actual: {estado_actual}")

        # Actualizar a fase_grupos
        print(f"\n🔄 Actualizando estado a 'fase_grupos'...")
        s.execute(text("""
            UPDATE torneo_categorias
            SET estado = 'fase_grupos'
            WHERE id = :cid
        """), {"cid": cat_id})

        s.commit()

        print(f"   ✅ Estado actualizado")
        print(f"\n{'=' * 70}")
        print(f"✅ LISTO - Ahora deberías poder generar fixture de otras categorías")
        print("=" * 70)

    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    actualizar()
