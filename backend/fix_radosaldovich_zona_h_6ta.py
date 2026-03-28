import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def main():
    s = Session()
    try:
        print("=" * 80)
        print("FIX PAREJA RADOSALDOVICH - ZONA H 6TA")
        print("=" * 80)
        
        # Buscar la pareja de Radosaldovich en Zona H de 6ta
        pareja_radosaldovich = s.execute(text("""
            SELECT 
                tp.id,
                tp.jugador1_id,
                tp.jugador2_id,
                pu1.nombre,
                pu1.apellido,
                pu2.nombre,
                pu2.apellido
            FROM torneos_parejas tp
            JOIN torneo_zona_parejas tzp ON tzp.pareja_id = tp.id
            JOIN torneo_zonas tz ON tzp.zona_id = tz.id
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN perfil_usuarios pu1 ON u1.id_usuario = pu1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            JOIN perfil_usuarios pu2 ON u2.id_usuario = pu2.id_usuario
            WHERE tc.torneo_id = :tid 
            AND tc.nombre = '6ta' 
            AND tz.nombre = 'Zona H'
            AND (LOWER(pu1.apellido) LIKE '%radosaldovich%' OR LOWER(pu1.nombre) LIKE '%radosaldovich%')
        """), {"tid": TORNEO_ID}).fetchone()
        
        if not pareja_radosaldovich:
            print("❌ Pareja de Radosaldovich no encontrada")
            return
        
        print(f"\n📋 Pareja encontrada (ID: {pareja_radosaldovich[0]}):")
        print(f"  Jugador 1: {pareja_radosaldovich[3]} {pareja_radosaldovich[4]} (ID: {pareja_radosaldovich[1]})")
        print(f"  Jugador 2: {pareja_radosaldovich[5]} {pareja_radosaldovich[6]} (ID: {pareja_radosaldovich[2]})")
        
        # Buscar o crear usuario "Desconocido"
        desconocido = s.execute(text("""
            SELECT u.id_usuario
            FROM usuarios u
            JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE LOWER(pu.nombre) = 'desconocido' AND LOWER(pu.apellido) = 'desconocido'
        """)).fetchone()
        
        if desconocido:
            desconocido_id = desconocido[0]
            print(f"\n✅ Usuario 'Desconocido' encontrado (ID: {desconocido_id})")
        else:
            # Crear usuario Desconocido
            print(f"\n📝 Creando usuario 'Desconocido'...")
            s.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash)
                VALUES ('desconocido', 'desconocido@temp.com', 'temp_hash')
            """))
            
            desconocido_id = s.execute(text("""
                SELECT id_usuario FROM usuarios WHERE nombre_usuario = 'desconocido'
            """)).scalar()
            
            # Crear perfil
            s.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                VALUES (:uid, 'Desconocido', 'Desconocido')
            """), {"uid": desconocido_id})
            
            print(f"✅ Usuario 'Desconocido' creado (ID: {desconocido_id})")
        
        # Actualizar pareja
        print(f"\n📝 Actualizando pareja {pareja_radosaldovich[0]}...")
        s.execute(text("""
            UPDATE torneos_parejas
            SET jugador2_id = :desconocido
            WHERE id = :pareja_id
        """), {"desconocido": desconocido_id, "pareja_id": pareja_radosaldovich[0]})
        
        print("✅ Pareja actualizada")
        
        s.commit()
        
        print("\n" + "=" * 80)
        print("✅ PAREJA RADOSALDOVICH CORREGIDA")
        print("=" * 80)
        print(f"Pareja {pareja_radosaldovich[0]}: Radosaldovich / Desconocido")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
