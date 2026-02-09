"""
Migra usuarios duplicados a sus cuentas reales:
- Jere Vera → jerevera97
- Emilio De la Fuente → usuario real
- Joaquin Coppede → usuario real  
- Damian Tapia → usuario real
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from sqlalchemy import text

def buscar_usuarios(db, nombre_busqueda):
    """Busca usuarios por nombre o apellido"""
    result = db.execute(text("""
        SELECT u.id_usuario, u.email, p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.nombre) LIKE LOWER(:busqueda) 
        OR LOWER(p.apellido) LIKE LOWER(:busqueda)
        ORDER BY u.id_usuario
    """), {"busqueda": f"%{nombre_busqueda}%"}).fetchall()
    return result

def main():
    db = SessionLocal()
    try:
        print("\n🔍 Buscando usuarios duplicados...\n")
        
        # Buscar cada usuario
        usuarios_buscar = [
            ("Jere", "Vera"),
            ("Emilio", "De la Fuente"),
            ("Joaquin", "Coppede"),
            ("Damian", "Tapia")
        ]
        
        for nombre, apellido in usuarios_buscar:
            print(f"\n📋 Buscando: {nombre} {apellido}")
            print("=" * 50)
            
            # Buscar por nombre
            usuarios_nombre = buscar_usuarios(db, nombre)
            # Buscar por apellido
            usuarios_apellido = buscar_usuarios(db, apellido)
            
            # Combinar y eliminar duplicados
            usuarios_dict = {}
            for u in usuarios_nombre + usuarios_apellido:
                usuarios_dict[u[0]] = u
            
            usuarios = list(usuarios_dict.values())
            
            if not usuarios:
                print(f"   ❌ No se encontraron usuarios")
                continue
            
            for u in usuarios:
                print(f"   ID {u[0]}: {u[2]} {u[3]} ({u[1]})")
        
        print("\n" + "=" * 50)
        print("\n📝 Para migrar usuarios, necesito que me indiques:")
        print("   1. ID del usuario DUPLICADO (el que se va a eliminar)")
        print("   2. ID del usuario REAL (al que se van a migrar los datos)")
        print("\nEjemplo de uso:")
        print("   python migrar_usuario_especifico.py <id_duplicado> <id_real>")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
