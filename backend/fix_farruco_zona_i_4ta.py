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
        print("FIX FARRUCO → PABLO FERREYRA - ZONA I 4TA")
        print("=" * 80)
        
        # Buscar la pareja con FARRUCO en Zona I de 4ta
        pareja_farruco = s.execute(text("""
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
            AND tc.nombre = '4ta' 
            AND tz.nombre = 'Zona I'
            AND (LOWER(pu1.apellido) LIKE '%farruco%' OR LOWER(pu2.apellido) LIKE '%farruco%'
                 OR LOWER(pu1.nombre) LIKE '%farruco%' OR LOWER(pu2.nombre) LIKE '%farruco%')
        """), {"tid": TORNEO_ID}).fetchone()
        
        if not pareja_farruco:
            print("❌ Pareja con FARRUCO no encontrada")
            return
        
        print(f"\n📋 Pareja encontrada (ID: {pareja_farruco[0]}):")
        print(f"  Jugador 1: {pareja_farruco[3]} {pareja_farruco[4]} (ID: {pareja_farruco[1]})")
        print(f"  Jugador 2: {pareja_farruco[5]} {pareja_farruco[6]} (ID: {pareja_farruco[2]})")
        
        # Verificar que Pablo Ferreyra existe con ID 866
        pablo_ferreyra = s.execute(text("""
            SELECT u.id_usuario, pu.nombre, pu.apellido
            FROM usuarios u
            JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE u.id_usuario = 866
        """)).fetchone()
        
        if not pablo_ferreyra:
            print("\n❌ Pablo Ferreyra (ID 866) no encontrado")
            return
        
        print(f"\n✅ Pablo Ferreyra encontrado: {pablo_ferreyra[1]} {pablo_ferreyra[2]} (ID: {pablo_ferreyra[0]})")
        
        # Determinar qué jugador es FARRUCO (jugador1 o jugador2)
        if 'farruco' in pareja_farruco[4].lower() or 'farruco' in pareja_farruco[3].lower():
            # FARRUCO es jugador2
            print(f"\n📝 Actualizando jugador2 de la pareja {pareja_farruco[0]}...")
            s.execute(text("""
                UPDATE torneos_parejas
                SET jugador2_id = 866
                WHERE id = :pareja_id
            """), {"pareja_id": pareja_farruco[0]})
        else:
            # FARRUCO es jugador1
            print(f"\n📝 Actualizando jugador1 de la pareja {pareja_farruco[0]}...")
            s.execute(text("""
                UPDATE torneos_parejas
                SET jugador1_id = 866
                WHERE id = :pareja_id
            """), {"pareja_id": pareja_farruco[0]})
        
        print("✅ Pareja actualizada")
        
        s.commit()
        
        print("\n" + "=" * 80)
        print("✅ PAREJA CORREGIDA")
        print("=" * 80)
        print(f"Pareja {pareja_farruco[0]}: FARRUCO → Pablo Ferreyra (ID 866)")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
