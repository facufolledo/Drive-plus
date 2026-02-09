"""
Recrea las semifinales vacías de Principiantes del torneo 37
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    try:
        # Verificar que no existan semifinales
        check = db.execute(text("""
            SELECT COUNT(*) FROM partidos 
            WHERE id_torneo = 37 
            AND categoria_id = 84 
            AND fase IN ('semis', 'semifinales')
        """)).scalar()
        
        if check > 0:
            print(f"⚠️  Ya existen {check} semifinales")
            return
        
        # Insertar con SQL raw para evitar problemas de constraint
        db.execute(text("""
            INSERT INTO partidos (
                id_torneo, categoria_id, fase, numero_partido,
                pareja1_id, pareja2_id, estado, fecha, id_creador, tipo
            ) VALUES
            (37, 84, 'semis', 1, NULL, NULL, 'pendiente', '2026-02-08', 1, 'torneo'),
            (37, 84, 'semis', 2, NULL, NULL, 'pendiente', '2026-02-08', 1, 'torneo')
        """))
        
        db.commit()
        
        print("✅ 2 semifinales vacías creadas exitosamente")
        print("   - Semifinal 1: TBD vs TBD")
        print("   - Semifinal 2: TBD vs TBD")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
