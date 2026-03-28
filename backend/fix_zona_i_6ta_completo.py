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
        print("FIX ZONA I - 6TA CATEGORÍA")
        print("=" * 80)
        
        # Obtener zona I
        zona_i = s.execute(text("""
            SELECT tz.id
            FROM torneo_zonas tz
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = 45 AND tc.nombre = '6ta' AND tz.nombre = 'Zona I'
        """)).scalar()
        
        print(f"\n✅ Zona I encontrada (ID: {zona_i})")
        
        # Buscar Nicolas Lucero
        nicolas_lucero = s.execute(text("""
            SELECT u.id_usuario, pu.nombre, pu.apellido
            FROM usuarios u
            JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE LOWER(pu.nombre) LIKE '%nicolas%' 
            AND LOWER(pu.apellido) LIKE '%lucero%'
            LIMIT 1
        """)).fetchone()
        
        if not nicolas_lucero:
            print("❌ Nicolas Lucero no encontrado")
            return
        
        print(f"✅ Nicolas Lucero encontrado (ID: {nicolas_lucero[0]})")
        
        # Buscar Luciano Paez
        luciano_paez = s.execute(text("""
            SELECT u.id_usuario, pu.nombre, pu.apellido
            FROM usuarios u
            JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE LOWER(pu.nombre) LIKE '%luciano%' 
            AND LOWER(pu.apellido) LIKE '%paez%'
            LIMIT 1
        """)).fetchone()
        
        if not luciano_paez:
            print("❌ Luciano Paez no encontrado")
            return
        
        print(f"✅ Luciano Paez encontrado (ID: {luciano_paez[0]})")
        
        # Verificar si ya existe la pareja
        pareja_existente = s.execute(text("""
            SELECT id FROM torneos_parejas
            WHERE torneo_id = :tid 
            AND jugador1_id = :j1 
            AND jugador2_id = :j2
        """), {"tid": TORNEO_ID, "j1": nicolas_lucero[0], "j2": luciano_paez[0]}).scalar()
        
        if pareja_existente:
            print(f"\n✅ Pareja ya existe (ID: {pareja_existente})")
            nueva_pareja_id = pareja_existente
        else:
            # Crear pareja
            print(f"\n📝 Creando pareja Nicolas Lucero / Luciano Paez...")
            s.execute(text("""
                INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id)
                VALUES (:tid, :j1, :j2)
            """), {"tid": TORNEO_ID, "j1": nicolas_lucero[0], "j2": luciano_paez[0]})
            
            nueva_pareja_id = s.execute(text("""
                SELECT id FROM torneos_parejas 
                WHERE torneo_id = :tid AND jugador1_id = :j1 AND jugador2_id = :j2
                ORDER BY id DESC LIMIT 1
            """), {"tid": TORNEO_ID, "j1": nicolas_lucero[0], "j2": luciano_paez[0]}).scalar()
            
            print(f"✅ Pareja creada (ID: {nueva_pareja_id})")
        
        # Verificar si ya está inscrita en la zona
        ya_inscrita = s.execute(text("""
            SELECT COUNT(*) FROM torneo_zona_parejas
            WHERE zona_id = :zid AND pareja_id = :pid
        """), {"zid": zona_i, "pid": nueva_pareja_id}).scalar()
        
        if ya_inscrita == 0:
            # Inscribir en zona
            s.execute(text("""
                INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
                VALUES (:zid, :pid)
            """), {"zid": zona_i, "pid": nueva_pareja_id})
            
            print("✅ Pareja inscrita en Zona I")
        else:
            print("✅ Pareja ya estaba inscrita en Zona I")
        
        # Actualizar partidos que referencian pareja 968 (si existe)
        print(f"\n📝 Actualizando partidos...")
        s.execute(text("""
            UPDATE partidos
            SET pareja1_id = :nueva_pareja
            WHERE pareja1_id = 968 AND zona_id = :zid
        """), {"nueva_pareja": nueva_pareja_id, "zid": zona_i})
        
        s.execute(text("""
            UPDATE partidos
            SET pareja2_id = :nueva_pareja
            WHERE pareja2_id = 968 AND zona_id = :zid
        """), {"nueva_pareja": nueva_pareja_id, "zid": zona_i})
        
        print("✅ Partidos actualizados")
        
        s.commit()
        
        print("\n" + "=" * 80)
        print("✅ ZONA I CORREGIDA")
        print("=" * 80)
        print(f"Pareja Nicolas Lucero / Luciano Paez (ID: {nueva_pareja_id}) inscrita en Zona I")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
