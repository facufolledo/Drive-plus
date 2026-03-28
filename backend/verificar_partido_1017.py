import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def main():
    s = Session()
    try:
        print("=" * 80)
        print("VERIFICAR PARTIDO 1017")
        print("=" * 80)
        
        # Ver info del partido
        partido = s.execute(text("""
            SELECT 
                p.id_partido,
                p.pareja1_id,
                p.pareja2_id,
                p.fecha_hora,
                p.cancha_id,
                tz.nombre as zona,
                tc.nombre as categoria
            FROM partidos p
            JOIN torneo_zonas tz ON p.zona_id = tz.id
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE p.id_partido = 1017
        """)).fetchone()
        
        if not partido:
            print("❌ Partido 1017 no encontrado")
            return
        
        print(f"\n📋 PARTIDO {partido[0]}:")
        print(f"  Categoría: {partido[6]}")
        print(f"  Zona: {partido[5]}")
        print(f"  Pareja 1 ID: {partido[1]}")
        print(f"  Pareja 2 ID: {partido[2]}")
        print(f"  Fecha/Hora: {partido[3]}")
        print(f"  Cancha ID: {partido[4]}")
        
        # Ver jugadores de pareja 1
        if partido[1]:
            pareja1 = s.execute(text("""
                SELECT 
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
                WHERE tp.id = :pid
            """), {"pid": partido[1]}).fetchone()
            
            if pareja1:
                print(f"\n  Pareja 1 (ID {partido[1]}):")
                print(f"    - {pareja1[1]} {pareja1[2]} (ID: {pareja1[0]})")
                print(f"    - {pareja1[4]} {pareja1[5]} (ID: {pareja1[3]})")
        
        # Ver jugadores de pareja 2
        if partido[2]:
            pareja2 = s.execute(text("""
                SELECT 
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
                WHERE tp.id = :pid
            """), {"pid": partido[2]}).fetchone()
            
            if pareja2:
                print(f"\n  Pareja 2 (ID {partido[2]}):")
                print(f"    - {pareja2[1]} {pareja2[2]} (ID: {pareja2[0]})")
                print(f"    - {pareja2[4]} {pareja2[5]} (ID: {pareja2[3]})")
        
        print("\n" + "=" * 80)
        print("DEBERÍA SER:")
        print("=" * 80)
        print("  Agustín Aguirre / Brian Barrera vs Juan Loto / Emanuel Reyes")
        print("  Sábado 12:00, Cancha 3")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
