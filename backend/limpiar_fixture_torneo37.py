"""
Limpiar fixture del torneo 37 para regenerarlo con restricciones
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def limpiar_fixture():
    session = Session()
    
    try:
        print("=" * 80)
        print("LIMPIANDO FIXTURE DEL TORNEO 37")
        print("=" * 80)
        
        # Contar partidos actuales
        partidos = session.execute(
            text("SELECT COUNT(*) FROM partidos WHERE id_torneo = 37")
        ).fetchone()
        
        print(f"\n📊 Partidos actuales: {partidos[0]}")
        
        if partidos[0] == 0:
            print("\n✅ No hay partidos para eliminar")
            return
        
        # Eliminar partidos
        session.execute(
            text("DELETE FROM partidos WHERE id_torneo = 37")
        )
        
        # Limpiar tablas de posiciones
        zonas = session.execute(
            text("SELECT id FROM torneo_zonas WHERE torneo_id = 37")
        ).fetchall()
        
        if zonas:
            zonas_ids = [z[0] for z in zonas]
            session.execute(
                text(f"DELETE FROM torneo_tabla_posiciones WHERE zona_id IN ({','.join(map(str, zonas_ids))})")
            )
        
        session.commit()
        
        print(f"\n✅ Fixture eliminado exitosamente")
        print(f"   • {partidos[0]} partidos eliminados")
        print(f"   • Tablas de posiciones limpiadas")
        print(f"\n💡 Ahora puedes regenerar el fixture desde el frontend")
        print(f"   con el botón 'Generar Fixture' que respetará las restricciones")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    limpiar_fixture()
