"""
Script para eliminar usuarios artificiales de 5ta que ya existen en la app
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

def eliminar_usuarios_artificiales():
    """Elimina usuarios artificiales que ya existen en la app"""
    session = Session()
    
    try:
        print("=" * 80)
        print("ELIMINAR USUARIOS ARTIFICIALES DE 5TA")
        print("=" * 80)
        
        # Usuarios artificiales a eliminar (los que tienen email @driveplus.temp)
        usuarios_artificiales = [
            "leandro.ruarte@driveplus.temp",
            "ignacio.villegas@driveplus.temp",
            "gaston.romero@driveplus.temp"
        ]
        
        eliminados = 0
        
        for email in usuarios_artificiales:
            # Buscar usuario
            usuario = session.execute(
                text("SELECT id_usuario, nombre_usuario FROM usuarios WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if usuario:
                usuario_id = usuario[0]
                username = usuario[1]
                
                # Verificar si tiene parejas en torneos
                parejas = session.execute(
                    text("""
                        SELECT COUNT(*) FROM parejas_torneo 
                        WHERE jugador1_id = :id OR jugador2_id = :id
                    """),
                    {"id": usuario_id}
                ).fetchone()[0]
                
                if parejas > 0:
                    print(f"⚠️  {email}: Tiene {parejas} parejas, no se puede eliminar")
                    continue
                
                # Eliminar perfil
                session.execute(
                    text("DELETE FROM perfil_usuario WHERE id_usuario = :id"),
                    {"id": usuario_id}
                )
                
                # Eliminar usuario
                session.execute(
                    text("DELETE FROM usuarios WHERE id_usuario = :id"),
                    {"id": usuario_id}
                )
                
                print(f"✅ Eliminado: {email} (ID: {usuario_id}, username: {username})")
                eliminados += 1
            else:
                print(f"⚠️  {email}: No encontrado")
        
        if eliminados > 0:
            confirmar = input(f"\n¿Confirmar eliminación de {eliminados} usuarios? (si/no): ").strip().lower()
            
            if confirmar == 'si':
                session.commit()
                print(f"\n✅ {eliminados} usuarios eliminados exitosamente")
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
    eliminar_usuarios_artificiales()
