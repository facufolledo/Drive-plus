"""
Script para eliminar usuarios duplicados de 5ta (los recién creados)
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

def eliminar_duplicados():
    """Elimina usuarios duplicados que acabamos de crear"""
    session = Session()
    
    try:
        print("=" * 80)
        print("ELIMINAR USUARIOS DUPLICADOS DE 5TA")
        print("=" * 80)
        
        # IDs de los usuarios duplicados que acabamos de crear
        usuarios_duplicados = [202, 207, 208]  # Ignacio Villegas, Leandro Ruarte, Gaston Romero
        
        eliminados = 0
        
        for usuario_id in usuarios_duplicados:
            # Buscar usuario
            usuario = session.execute(
                text("SELECT id_usuario, nombre_usuario, email FROM usuarios WHERE id_usuario = :id"),
                {"id": usuario_id}
            ).fetchone()
            
            if usuario:
                username = usuario[1]
                email = usuario[2]
                
                # Eliminar usuario directamente (CASCADE debería eliminar el perfil)
                session.execute(
                    text("DELETE FROM usuarios WHERE id_usuario = :id"),
                    {"id": usuario_id}
                )
                
                print(f"✅ Eliminado: ID {usuario_id} - {username} ({email})")
                eliminados += 1
            else:
                print(f"⚠️  ID {usuario_id}: No encontrado")
        
        if eliminados > 0:
            confirmar = input(f"\n¿Confirmar eliminación de {eliminados} usuarios? (si/no): ").strip().lower()
            
            if confirmar == 'si':
                session.commit()
                print(f"\n✅ {eliminados} usuarios eliminados exitosamente")
                print("\n📝 Usuarios reales que debes usar:")
                print("   - Ignacio Villegas: ignaciovillegas")
                print("   - Leandro Ruarte: leandroruarte")
                print("   - Gaston Romero: gastonromero")
            else:
                session.rollback()
                print("\n❌ Cambios descartados")
        else:
            print("\n⚠️  No se eliminó ningún usuario")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    eliminar_duplicados()
