"""
Borra todos los playoffs de Principiantes y los recrea desde cero
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
        # 1. Borrar todos los partidos de playoffs de Principiantes
        print("\n🗑️  Borrando playoffs existentes...")
        result = db.execute(text("""
            DELETE FROM partidos 
            WHERE id_torneo = 37 
            AND categoria_id = 84 
            AND fase IN ('cuartos', '4tos', 'semis', 'semifinales', 'final')
        """))
        db.commit()
        print(f"   ✅ {result.rowcount} partidos borrados")
        
        # 2. Crear cuartos de final (4 partidos)
        print("\n📋 Creando cuartos de final...")
        db.execute(text("""
            INSERT INTO partidos (
                id_torneo, categoria_id, fase, numero_partido,
                pareja1_id, pareja2_id, estado, fecha, id_creador, tipo
            ) VALUES
            -- Cuarto 1: Jere Vera / Marcos Calderón vs Victoria Cavalleri / Gula Saracho
            (37, 84, '4tos', 1, 495, 470, 'pendiente', '2026-02-08', 1, 'torneo'),
            -- Cuarto 2: Exequiel Damian / Santiago Mazza vs Fabián Alejandro Villafañe / Franco Direnzo
            (37, 84, '4tos', 2, 476, 478, 'pendiente', '2026-02-08', 1, 'torneo'),
            -- Cuarto 3: Dario Barrionuevo / Matias Vega vs Sergio Pansa / Sebastian Corzo
            (37, 84, '4tos', 3, 477, 497, 'pendiente', '2026-02-08', 1, 'torneo'),
            -- Cuarto 4: Maximiliano Yelamo / Jorge Paz vs Carlos Fernandez / Leo Mena
            (37, 84, '4tos', 4, 468, 475, 'pendiente', '2026-02-08', 1, 'torneo')
        """))
        db.commit()
        print("   ✅ 4 cuartos de final creados")
        
        # 3. Crear semifinales (2 partidos vacíos)
        print("\n📋 Creando semifinales...")
        db.execute(text("""
            INSERT INTO partidos (
                id_torneo, categoria_id, fase, numero_partido,
                pareja1_id, pareja2_id, estado, fecha, id_creador, tipo
            ) VALUES
            (37, 84, 'semis', 1, NULL, NULL, 'pendiente', '2026-02-08', 1, 'torneo'),
            (37, 84, 'semis', 2, NULL, NULL, 'pendiente', '2026-02-08', 1, 'torneo')
        """))
        db.commit()
        print("   ✅ 2 semifinales creadas")
        
        # 4. Crear final (1 partido vacío)
        print("\n📋 Creando final...")
        db.execute(text("""
            INSERT INTO partidos (
                id_torneo, categoria_id, fase, numero_partido,
                pareja1_id, pareja2_id, estado, fecha, id_creador, tipo
            ) VALUES
            (37, 84, 'final', 1, NULL, NULL, 'pendiente', '2026-02-08', 1, 'torneo')
        """))
        db.commit()
        print("   ✅ Final creada")
        
        print("\n✅ Bracket de Principiantes recreado exitosamente")
        print("\n📊 Resumen:")
        print("   - 4 cuartos de final con parejas asignadas")
        print("   - 2 semifinales vacías (TBD)")
        print("   - 1 final vacía (TBD)")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
