"""
Script para buscar usuarios reales en la app
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

def buscar_usuarios_reales():
    """Busca usuarios reales que ya existen en la app"""
    session = Session()
    
    try:
        print("=" * 80)
        print("BUSCAR USUARIOS REALES EN LA APP")
        print("=" * 80)
        
        # Buscar variaciones de los nombres
        nombres_buscar = [
            ('ignacio', 'villegas'),
            ('leandro', 'ruarte'),
            ('gaston', 'romero'),
            ('bautista', 'wamba')
        ]
        
        for nombre, apellido in nombres_buscar:
            print(f"\n🔍 Buscando: {nombre} {apellido}")
            
            # Buscar por nombre_usuario con variaciones
            variaciones = [
                f"{nombre}{apellido}",
                f"{nombre}.{apellido}",
                f"{nombre}_{apellido}",
                f"{apellido}{nombre}",
                f"{nombre[0]}{apellido}",
            ]
            
            encontrados = set()
            
            for var in variaciones:
                result = session.execute(
                    text("SELECT id_usuario, nombre_usuario, email FROM usuarios WHERE nombre_usuario LIKE :pattern"),
                    {"pattern": f"%{var}%"}
                ).fetchall()
                
                for user_id, username, email in result:
                    if username not in encontrados:
                        encontrados.add(username)
                        es_artificial = "@driveplus.temp" in email
                        tipo = "🤖 ARTIFICIAL" if es_artificial else "✅ REAL"
                        print(f"  {tipo} {username} (ID: {user_id}, email: {email})")
            
            if not encontrados:
                print(f"  ❌ No se encontró ningún usuario")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    buscar_usuarios_reales()
