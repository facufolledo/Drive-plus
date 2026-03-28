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
        print("VERIFICAR ZONA I Y J - 6TA CATEGORÍA")
        print("=" * 80)
        
        # Ver Zona I
        print("\n📍 ZONA I:")
        zona_i = s.execute(text("""
            SELECT tz.id
            FROM torneo_zonas tz
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = 45 AND tc.nombre = '6ta' AND tz.nombre = 'Zona I'
        """)).scalar()
        
        if zona_i:
            parejas_i = s.execute(text("""
                SELECT 
                    tp.id,
                    u1.id_usuario,
                    pu1.nombre,
                    pu1.apellido,
                    u2.id_usuario,
                    pu2.nombre,
                    pu2.apellido
                FROM torneo_zona_parejas tzp
                JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
                JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
                JOIN perfil_usuarios pu1 ON u1.id_usuario = pu1.id_usuario
                JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
                JOIN perfil_usuarios pu2 ON u2.id_usuario = pu2.id_usuario
                WHERE tzp.zona_id = :zid
            """), {"zid": zona_i}).fetchall()
            
            for p in parejas_i:
                print(f"  Pareja {p[0]}: {p[2]} {p[3]} (ID: {p[1]}) / {p[5]} {p[6]} (ID: {p[4]})")
            
            # Ver partidos
            partidos_i = s.execute(text("""
                SELECT 
                    p.id_partido,
                    p.pareja1_id,
                    p.pareja2_id,
                    p.fecha_hora,
                    p.cancha_id
                FROM partidos p
                WHERE p.zona_id = :zid
                ORDER BY p.fecha_hora
            """), {"zid": zona_i}).fetchall()
            
            print(f"\n  Partidos:")
            for p in partidos_i:
                print(f"    - Partido {p[0]}: Pareja {p[1]} vs {p[2]} | {p[3]} | Cancha {p[4]}")
        
        # Ver Zona J
        print("\n📍 ZONA J:")
        zona_j = s.execute(text("""
            SELECT tz.id
            FROM torneo_zonas tz
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = 45 AND tc.nombre = '6ta' AND tz.nombre = 'Zona J'
        """)).scalar()
        
        if zona_j:
            parejas_j = s.execute(text("""
                SELECT 
                    tp.id,
                    u1.id_usuario,
                    pu1.nombre,
                    pu1.apellido,
                    u2.id_usuario,
                    pu2.nombre,
                    pu2.apellido
                FROM torneo_zona_parejas tzp
                JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
                JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
                JOIN perfil_usuarios pu1 ON u1.id_usuario = pu1.id_usuario
                JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
                JOIN perfil_usuarios pu2 ON u2.id_usuario = pu2.id_usuario
                WHERE tzp.zona_id = :zid
            """), {"zid": zona_j}).fetchall()
            
            for p in parejas_j:
                print(f"  Pareja {p[0]}: {p[2]} {p[3]} (ID: {p[1]}) / {p[5]} {p[6]} (ID: {p[4]})")
            
            # Ver partidos
            partidos_j = s.execute(text("""
                SELECT 
                    p.id_partido,
                    p.pareja1_id,
                    p.pareja2_id,
                    p.fecha_hora,
                    p.cancha_id
                FROM partidos p
                WHERE p.zona_id = :zid
                ORDER BY p.fecha_hora
            """), {"zid": zona_j}).fetchall()
            
            print(f"\n  Partidos:")
            for p in partidos_j:
                print(f"    - Partido {p[0]}: Pareja {p[1]} vs {p[2]} | {p[3]} | Cancha {p[4]}")
        
        print("\n" + "=" * 80)
        print("DEBERÍA SER:")
        print("=" * 80)
        print("Zona I: Jeremias Salazar / Carrizo Jeremias")
        print("        Matias Rosa / Miguel Estrada")
        print("        Nicolas Lucero / Luciano Paez")
        print("\nZona J: Santino Gonzalez / Ramiro Gonzales vs Navarro Martin / Luna Gustavo")
        print("        Viernes 16:00, Cancha 2")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
