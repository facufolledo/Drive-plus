"""
Script para corregir el rating de usuarios artificiales de 7ma
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

def corregir_rating_7ma():
    """Corrige el rating de usuarios artificiales de 7ma de 1200 a 1099"""
    session = Session()
    
    try:
        print("=" * 80)
        print("CORREGIR RATING DE USUARIOS ARTIFICIALES DE 7MA")
        print("=" * 80)
        
        # Lista de emails de usuarios artificiales de 7ma que creamos
        emails_7ma = [
            "juanpablo.romerojr@driveplus.temp",
            "juan.romero@driveplus.temp",
            "diego.bicet@driveplus.temp",
            "juan.cejas@driveplus.temp",
            "eric.leterrucci@driveplus.temp",
            "facundo.guerrero@driveplus.temp",
            "agustin.barrera@driveplus.temp",
            "valentin.granillo@driveplus.temp",
            "martin.sanchez@driveplus.temp",
            "andres.bordon@driveplus.temp",
            "emilio.delafuente@driveplus.temp",
            "joaquin.coppede@driveplus.temp",
            "matias.giordano@driveplus.temp",
            "damian.tapia@driveplus.temp"
        ]
        
        # Buscar estos usuarios
        placeholders = ','.join([f"'{email}'" for email in emails_7ma])
        usuarios = session.execute(
            text(f"""
                SELECT id_usuario, nombre_usuario, email, rating
                FROM usuarios
                WHERE email IN ({placeholders})
                ORDER BY id_usuario
            """)
        ).fetchall()
        
        if not usuarios:
            print("\nNo se encontraron usuarios artificiales de 7ma")
            return
        
        print(f"\nUsuarios de 7ma encontrados: {len(usuarios)}")
        print("-" * 80)
        
        for user_id, username, email, rating in usuarios:
            print(f"  - {username:30} (ID: {user_id:3}, rating actual: {rating})")
        
        print("\n" + "=" * 80)
        confirmar = input(f"¿Cambiar rating de {len(usuarios)} usuarios a 1099? (si/no): ").strip().lower()
        
        if confirmar != 'si':
            print("\nCambios cancelados")
            return
        
        # Actualizar rating
        session.execute(
            text(f"""
                UPDATE usuarios
                SET rating = 1099
                WHERE email IN ({placeholders})
            """)
        )
        
        session.commit()
        
        print(f"\n✅ Rating actualizado para {len(usuarios)} usuarios")
        
        # Verificar cambios
        print("\nVerificando cambios...")
        verificacion = session.execute(
            text(f"""
                SELECT nombre_usuario, rating
                FROM usuarios
                WHERE email IN ({placeholders})
                ORDER BY id_usuario
            """)
        ).fetchall()
        
        print("\nRatings actualizados:")
        for username, rating in verificacion:
            print(f"  - {username:30} rating: {rating}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    corregir_rating_7ma()
