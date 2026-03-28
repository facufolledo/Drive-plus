#!/usr/bin/env python3
"""
Buscar Jeremías Arrebola (con acento)
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
        print("BUSCAR JEREMÍAS ARREBOLA")
        print("=" * 80)
        
        # Buscar con diferentes variaciones
        variaciones = [
            "jeremias arrebola",
            "jeremías arrebola",
            "jere arrebola",
            "%jerem%arrebola%",
        ]
        
        for var in variaciones:
            print(f"\n🔍 Buscando: {var}")
            
            # Buscar en perfil_usuarios
            result = s.execute(text("""
                SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating,
                       p.nombre, p.apellido,
                       CASE 
                           WHEN u.email LIKE '%@driveplus.temp' THEN 'TEMP'
                           WHEN u.password_hash IS NULL OR u.password_hash = '' THEN 'FIREBASE'
                           ELSE 'LOCAL'
                       END as tipo
                FROM usuarios u
                LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
                WHERE LOWER(CONCAT(COALESCE(p.nombre, ''), ' ', COALESCE(p.apellido, ''))) LIKE LOWER(:var)
                   OR LOWER(u.nombre_usuario) LIKE LOWER(:var)
            """), {"var": f"%{var}%"}).fetchall()
            
            if result:
                for r in result:
                    # Contar partidos
                    partidos = s.execute(text("""
                        SELECT COUNT(DISTINCT p.id_partido) as total
                        FROM partidos p
                        JOIN torneos_parejas tp ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
                        WHERE (tp.jugador1_id = :uid OR tp.jugador2_id = :uid)
                    """), {"uid": r.id_usuario}).fetchone()
                    
                    print(f"   ✅ ID={r.id_usuario}, user={r.nombre_usuario}")
                    print(f"      Nombre: {r.nombre} {r.apellido}")
                    print(f"      Rating: {r.rating}, Tipo: {r.tipo}")
                    print(f"      Partidos: {partidos.total if partidos else 0}")
            else:
                print(f"   ❌ No encontrado")
        
        # Buscar todos los Arrebola
        print("\n" + "=" * 80)
        print("TODOS LOS ARREBOLA")
        print("=" * 80)
        
        arrebolas = s.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating,
                   p.nombre, p.apellido,
                   CASE 
                       WHEN u.email LIKE '%@driveplus.temp' THEN 'TEMP'
                       WHEN u.password_hash IS NULL OR u.password_hash = '' THEN 'FIREBASE'
                       ELSE 'LOCAL'
                   END as tipo
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.apellido) LIKE '%arrebola%'
               OR LOWER(u.nombre_usuario) LIKE '%arrebola%'
            ORDER BY p.nombre, p.apellido
        """)).fetchall()
        
        for a in arrebolas:
            partidos = s.execute(text("""
                SELECT COUNT(DISTINCT p.id_partido) as total
                FROM partidos p
                JOIN torneos_parejas tp ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
                WHERE (tp.jugador1_id = :uid OR tp.jugador2_id = :uid)
            """), {"uid": a.id_usuario}).fetchone()
            
            print(f"\n   ID={a.id_usuario}, user={a.nombre_usuario}")
            print(f"   Nombre: {a.nombre} {a.apellido}")
            print(f"   Rating: {a.rating}, Tipo: {a.tipo}")
            print(f"   Partidos: {partidos.total if partidos else 0}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
