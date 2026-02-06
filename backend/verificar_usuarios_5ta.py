"""
Script para verificar usuarios de 5ta categoría
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

def verificar_usuarios_5ta():
    """Verifica qué usuarios de 5ta existen y cuáles son artificiales"""
    session = Session()
    
    try:
        print("=" * 80)
        print("VERIFICAR USUARIOS DE 5TA CATEGORÍA")
        print("=" * 80)
        
        # Usuarios que deberían existir
        usuarios_esperados = [
            'agustinchumbita', 'lucasmartinez', 'tiagocordoba', 'marceloaballay',
            'tomasspeziale', 'valentinzarate', 'bautistaw amba', 'bautistaoliva',
            'juancalderon', 'ignaciovillegas', 'enzovallejos', 'juanmedina',
            'emilianomerlo', 'gabrielfernandez', 'leandroruarte', 'gastonromero'
        ]
        
        print("\n🔍 Verificando usuarios:")
        print("-" * 80)
        
        encontrados = []
        no_encontrados = []
        
        for username in usuarios_esperados:
            result = session.execute(
                text("SELECT id_usuario, email FROM usuarios WHERE nombre_usuario = :username"),
                {"username": username}
            ).fetchone()
            
            if result:
                user_id, email = result
                es_artificial = "@driveplus.temp" in email
                tipo = "🤖 ARTIFICIAL" if es_artificial else "✅ REAL"
                print(f"{tipo} {username:20} (ID: {user_id:3}, email: {email})")
                encontrados.append((username, user_id, email, es_artificial))
            else:
                print(f"❌ NO EXISTE {username}")
                no_encontrados.append(username)
        
        print("\n" + "=" * 80)
        print(f"📊 RESUMEN:")
        print(f"   Encontrados: {len(encontrados)}")
        print(f"   No encontrados: {len(no_encontrados)}")
        
        # Contar artificiales
        artificiales = [u for u in encontrados if u[3]]
        reales = [u for u in encontrados if not u[3]]
        
        print(f"   Usuarios reales: {len(reales)}")
        print(f"   Usuarios artificiales: {len(artificiales)}")
        
        if artificiales:
            print("\n⚠️  USUARIOS ARTIFICIALES A REVISAR:")
            for username, user_id, email, _ in artificiales:
                print(f"   - {username} (ID: {user_id}, email: {email})")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verificar_usuarios_5ta()
