#!/usr/bin/env python3
"""
Verificar cuál es el Paez correcto (Luciano vs Rodrigo)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

def main():
    s = Session()
    try:
        print("=" * 80)
        print("BUSCAR TODOS LOS PAEZ")
        print("=" * 80)
        
        paez = s.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating,
                   p.nombre, p.apellido,
                   CASE 
                       WHEN u.email LIKE '%@driveplus.temp' THEN 'TEMP'
                       WHEN u.password_hash IS NULL OR u.password_hash = '' THEN 'FIREBASE'
                       ELSE 'LOCAL'
                   END as tipo
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.apellido) LIKE '%paez%'
               OR LOWER(u.nombre_usuario) LIKE '%paez%'
            ORDER BY p.nombre, p.apellido
        """)).fetchall()
        
        print(f"\n📋 Usuarios Paez encontrados: {len(paez)}\n")
        
        for pa in paez:
            print(f"   ID={pa.id_usuario}, user={pa.nombre_usuario}")
            print(f"   Nombre: {pa.nombre} {pa.apellido}")
            print(f"   Rating: {pa.rating}, Tipo: {pa.tipo}")
            print(f"   Email: {pa.email}")
            
            # Ver si tiene pareja en torneo 45
            parejas = s.execute(text("""
                SELECT tp.id, tc.nombre as categoria
                FROM torneos_parejas tp
                LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
                WHERE tp.torneo_id = 45
                  AND (tp.jugador1_id = :uid OR tp.jugador2_id = :uid)
            """), {"uid": pa.id_usuario}).fetchall()
            
            if parejas:
                for par in parejas:
                    print(f"   ✅ Pareja en T45: ID={par.id}, Categoría={par.categoria}")
            else:
                print(f"   ❌ Sin pareja en T45")
            print()
        
        # Verificar pareja 822 específicamente
        print("=" * 80)
        print("PAREJA 822 (Nicolas Lucero)")
        print("=" * 80)
        
        pareja = s.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
                   u1.nombre_usuario as j1_user, p1.nombre as j1_nombre, p1.apellido as j1_apellido,
                   u2.nombre_usuario as j2_user, p2.nombre as j2_nombre, p2.apellido as j2_apellido,
                   tc.nombre as categoria
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            LEFT JOIN perfil_usuarios p1 ON u1.id_usuario = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON u2.id_usuario = p2.id_usuario
            LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
            WHERE tp.id = 822
        """)).fetchone()
        
        if pareja:
            print(f"\n   Pareja ID: {pareja.id}")
            print(f"   Categoría: {pareja.categoria}")
            print(f"   J1: {pareja.j1_nombre} {pareja.j1_apellido} (ID={pareja.jugador1_id}, user={pareja.j1_user})")
            print(f"   J2: {pareja.j2_nombre} {pareja.j2_apellido} (ID={pareja.jugador2_id}, user={pareja.j2_user})")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
