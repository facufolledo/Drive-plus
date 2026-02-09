"""
Borra las semifinales de Principiantes del torneo 37
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from src.models.driveplus_models import Partido

def main():
    db = SessionLocal()
    try:
        # Buscar semifinales de Principiantes (categoría 84, torneo 37)
        semis = db.query(Partido).filter(
            Partido.id_torneo == 37,
            Partido.categoria_id == 84,
            Partido.fase.in_(["semifinales", "semis"])
        ).all()
        
        if not semis:
            print("❌ No se encontraron semifinales para borrar")
            return
        
        print(f"\n🔍 Encontradas {len(semis)} semifinales:")
        for s in semis:
            print(f"  - Partido {s.numero_partido}: {s.pareja1_id} vs {s.pareja2_id} (id_partido={s.id_partido})")
        
        confirmar = input("\n¿Borrar estas semifinales? (s/n): ").strip().lower()
        if confirmar != 's':
            print("Cancelado")
            return
        
        for s in semis:
            db.delete(s)
        
        db.commit()
        print(f"\n✅ {len(semis)} semifinales borradas exitosamente")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
