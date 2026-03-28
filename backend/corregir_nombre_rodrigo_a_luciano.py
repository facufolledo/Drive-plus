#!/usr/bin/env python3
"""
Corregir nombre de Rodrigo Paez a Luciano Paez
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

USER_ID = 160

def main():
    s = Session()
    try:
        print("=" * 80)
        print("CORREGIR NOMBRE: RODRIGO -> LUCIANO PAEZ")
        print("=" * 80)
        
        # Verificar datos actuales
        actual = s.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": USER_ID}).fetchone()
        
        print(f"\n📋 Datos actuales:")
        print(f"   ID: {actual.id_usuario}")
        print(f"   Username: {actual.nombre_usuario}")
        print(f"   Email: {actual.email}")
        print(f"   Nombre: {actual.nombre} {actual.apellido}")
        
        # Actualizar nombre
        print(f"\n🔄 Actualizando nombre a 'Luciano'...")
        
        s.execute(text("""
            UPDATE perfil_usuarios
            SET nombre = 'Luciano'
            WHERE id_usuario = :uid
        """), {"uid": USER_ID})
        
        s.commit()
        
        # Verificar actualización
        nuevo = s.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": USER_ID}).fetchone()
        
        print(f"\n✅ Datos actualizados:")
        print(f"   ID: {nuevo.id_usuario}")
        print(f"   Username: {nuevo.nombre_usuario}")
        print(f"   Email: {nuevo.email}")
        print(f"   Nombre: {nuevo.nombre} {nuevo.apellido}")
        
        print("\n" + "=" * 80)
        print("✅ ACTUALIZACIÓN COMPLETADA")
        print("=" * 80)
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
