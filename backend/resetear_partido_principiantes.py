"""
Resetea el resultado del partido Dario Barrionuevo/Matias Vega vs Sergio Pansa/Sebastian Corzo
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
        # Buscar el partido (cuarto 3: Barrionuevo vs Pansa)
        # pareja1_id=477 (Barrionuevo/Vega), pareja2_id=497 (Pansa/Corzo)
        
        print("\n🔍 Buscando el partido...")
        partido = db.execute(text("""
            SELECT id_partido, pareja1_id, pareja2_id, estado, ganador_pareja_id
            FROM partidos
            WHERE id_torneo = 37
            AND categoria_id = 84
            AND fase = '4tos'
            AND numero_partido = 3
        """)).fetchone()
        
        if not partido:
            print("❌ No se encontró el partido")
            return
        
        print(f"\n📋 Partido encontrado:")
        print(f"   ID: {partido[0]}")
        print(f"   Pareja 1 (477 - Barrionuevo/Vega): {partido[1]}")
        print(f"   Pareja 2 (497 - Pansa/Corzo): {partido[2]}")
        print(f"   Estado: {partido[3]}")
        print(f"   Ganador: {partido[4]}")
        
        confirmar = input("\n¿Resetear este partido a pendiente? (s/n): ").strip().lower()
        if confirmar != 's':
            print("Cancelado")
            return
        
        # Resetear el partido
        db.execute(text("""
            UPDATE partidos
            SET estado = 'pendiente',
                ganador_pareja_id = NULL,
                elo_aplicado = FALSE
            WHERE id_partido = :id_partido
        """), {"id_partido": partido[0]})
        
        # También limpiar la semifinal si ya se asignó el ganador
        db.execute(text("""
            UPDATE partidos
            SET pareja1_id = NULL
            WHERE id_torneo = 37
            AND categoria_id = 84
            AND fase = 'semis'
            AND numero_partido = 2
            AND pareja1_id = :ganador_id
        """), {"ganador_id": partido[4]})
        
        db.execute(text("""
            UPDATE partidos
            SET pareja2_id = NULL
            WHERE id_torneo = 37
            AND categoria_id = 84
            AND fase = 'semis'
            AND numero_partido = 2
            AND pareja2_id = :ganador_id
        """), {"ganador_id": partido[4]})
        
        db.commit()
        
        print("\n✅ Partido reseteado exitosamente")
        print("   - Estado: pendiente")
        print("   - Ganador removido")
        print("   - Ganador removido de semifinal")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
