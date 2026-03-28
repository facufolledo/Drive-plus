import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45
VIERNES = "2026-03-06"

def main():
    s = Session()
    try:
        print("=" * 80)
        print("FIX ZONA I Y J - 6TA CATEGORÍA")
        print("=" * 80)
        
        # 1. Verificar pareja 968 (debería ser Nicolas Lucero / Luciano Paez)
        print("\n🔍 Verificando pareja 968...")
        pareja_968 = s.execute(text("""
            SELECT 
                tp.id,
                u1.id_usuario,
                pu1.nombre,
                pu1.apellido,
                u2.id_usuario,
                pu2.nombre,
                pu2.apellido
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN perfil_usuarios pu1 ON u1.id_usuario = pu1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            JOIN perfil_usuarios pu2 ON u2.id_usuario = pu2.id_usuario
            WHERE tp.id = 968
        """)).fetchone()
        
        if pareja_968:
            print(f"  Pareja 968: {pareja_968[2]} {pareja_968[3]} / {pareja_968[5]} {pareja_968[6]}")
            
            # Buscar Nicolas Lucero
            nicolas_lucero = s.execute(text("""
                SELECT u.id_usuario, pu.nombre, pu.apellido
                FROM usuarios u
                JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
                WHERE LOWER(pu.nombre) LIKE '%nicolas%' 
                AND LOWER(pu.apellido) LIKE '%lucero%'
                LIMIT 1
            """)).fetchone()
            
            if nicolas_lucero:
                print(f"\n✅ Nicolas Lucero encontrado (ID: {nicolas_lucero[0]})")
                
                # Buscar Luciano Paez
                luciano_paez = s.execute(text("""
                    SELECT u.id_usuario, pu.nombre, pu.apellido
                    FROM usuarios u
                    JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
                    WHERE LOWER(pu.nombre) LIKE '%luciano%' 
                    AND LOWER(pu.apellido) LIKE '%paez%'
                    LIMIT 1
                """)).fetchone()
                
                if luciano_paez:
                    print(f"✅ Luciano Paez encontrado (ID: {luciano_paez[0]})")
                    
                    # Actualizar pareja 968
                    print(f"\n📝 Actualizando pareja 968...")
                    s.execute(text("""
                        UPDATE torneos_parejas
                        SET jugador1_id = :j1, jugador2_id = :j2
                        WHERE id = 968
                    """), {"j1": nicolas_lucero[0], "j2": luciano_paez[0]})
                    
                    print("✅ Pareja 968 actualizada a Nicolas Lucero / Luciano Paez")
                else:
                    print("❌ Luciano Paez no encontrado")
            else:
                print("❌ Nicolas Lucero no encontrado")
        else:
            print("❌ Pareja 968 no encontrada")
        
        # 2. Corregir horario de Zona J (partido 997)
        print("\n📝 Corrigiendo horario de Zona J (partido 997)...")
        s.execute(text("""
            UPDATE partidos
            SET fecha_hora = :fecha_hora,
                fecha = :fecha
            WHERE id_partido = 997
        """), {
            "fecha_hora": f"{VIERNES} 16:00:00",
            "fecha": VIERNES
        })
        
        print("✅ Partido 997 actualizado a Viernes 16:00")
        
        s.commit()
        
        print("\n" + "=" * 80)
        print("✅ ZONA I Y J CORREGIDAS")
        print("=" * 80)
        print("Zona I: Pareja 968 ahora es Nicolas Lucero / Luciano Paez")
        print("Zona J: Partido 997 ahora es Viernes 16:00")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
