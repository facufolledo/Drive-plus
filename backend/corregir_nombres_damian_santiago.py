"""
Corrige los nombres de Exequiel Damian y Santiago Mazza
Nombres correctos: Damian Agostini y Nazareno Tanquia
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
        # Buscar los usuarios por nombre
        print("\n🔍 Buscando usuarios...")
        
        damian = db.execute(text("""
            SELECT p.id_usuario, p.nombre, p.apellido
            FROM perfil_usuarios p
            WHERE p.nombre ILIKE '%exequiel%' AND p.apellido ILIKE '%damian%'
        """)).fetchone()
        
        santiago = db.execute(text("""
            SELECT p.id_usuario, p.nombre, p.apellido
            FROM perfil_usuarios p
            WHERE p.nombre ILIKE '%santiago%' AND p.apellido ILIKE '%mazza%'
        """)).fetchone()
        
        if not damian:
            print("❌ No se encontró a Exequiel Damian")
            return
        
        if not santiago:
            print("❌ No se encontró a Santiago Mazza")
            return
        
        print(f"\n📋 Usuarios encontrados:")
        print(f"   1. ID {damian[0]}: {damian[1]} {damian[2]}")
        print(f"   2. ID {santiago[0]}: {santiago[1]} {santiago[2]}")
        
        print(f"\n✏️  Cambios a realizar:")
        print(f"   1. {damian[1]} {damian[2]} → Damian Agostini")
        print(f"   2. {santiago[1]} {santiago[2]} → Nazareno Tanquia")
        
        confirmar = input("\n¿Aplicar estos cambios? (s/n): ").strip().lower()
        if confirmar != 's':
            print("Cancelado")
            return
        
        # Actualizar nombres en perfil_usuarios
        db.execute(text("""
            UPDATE perfil_usuarios
            SET nombre = 'Damian', apellido = 'Agostini'
            WHERE id_usuario = :id_usuario
        """), {"id_usuario": damian[0]})
        
        db.execute(text("""
            UPDATE perfil_usuarios
            SET nombre = 'Nazareno', apellido = 'Tanquia'
            WHERE id_usuario = :id_usuario
        """), {"id_usuario": santiago[0]})
        
        db.commit()
        
        print("\n✅ Nombres actualizados exitosamente")
        print("   - Damian Agostini")
        print("   - Nazareno Tanquia")
        print("\n📝 Nota: Los cambios se reflejan automáticamente en:")
        print("   - Perfil de usuario")
        print("   - Parejas de torneos")
        print("   - Partidos")
        print("   - Historial de rating")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
