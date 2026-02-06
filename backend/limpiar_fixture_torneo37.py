"""
Script para eliminar el fixture del torneo 37
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno
load_dotenv()

# Configurar base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no configurada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def limpiar_fixture_torneo37():
    """Elimina todos los partidos del torneo 37"""
    db = SessionLocal()
    
    try:
        print("\n🔍 Verificando partidos del torneo 37...")
        
        # Contar partidos existentes
        result = db.execute(text("""
            SELECT COUNT(*) as total
            FROM partidos
            WHERE id_torneo = 37
        """))
        total_antes = result.fetchone()[0]
        
        print(f"   📊 Partidos encontrados: {total_antes}")
        
        if total_antes == 0:
            print("   ✅ No hay partidos para eliminar")
            return
        
        # Confirmar eliminación
        print(f"\n⚠️  Se eliminarán {total_antes} partidos del torneo 37")
        confirmacion = input("¿Continuar? (s/n): ")
        
        if confirmacion.lower() != 's':
            print("❌ Operación cancelada")
            return
        
        # Eliminar partidos
        print("\n🗑️  Eliminando partidos...")
        db.execute(text("""
            DELETE FROM partidos
            WHERE id_torneo = 37
        """))
        db.commit()
        
        # Verificar eliminación
        result = db.execute(text("""
            SELECT COUNT(*) as total
            FROM partidos
            WHERE id_torneo = 37
        """))
        total_despues = result.fetchone()[0]
        
        print(f"\n✅ Fixture eliminado exitosamente")
        print(f"   Partidos eliminados: {total_antes}")
        print(f"   Partidos restantes: {total_despues}")
        
        print("\n📝 Ahora puedes regenerar el fixture con:")
        print("   python backend/test_generar_fixture_torneo37.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    limpiar_fixture_torneo37()
