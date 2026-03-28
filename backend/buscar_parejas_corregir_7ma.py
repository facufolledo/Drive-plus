"""
Buscar parejas que necesitan corrección en 7ma torneo 46
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine, text

env_file = os.path.join(os.path.dirname(__file__), '.env.production')
DATABASE_URL = None
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DATABASE_URL = line.split('=', 1)[1].strip().strip('"').strip("'")
                break

engine = create_engine(DATABASE_URL)

def main():
    print("=" * 80)
    print("BUSCANDO PAREJAS EN 7MA TORNEO 46")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Buscar Juin + López
        print("\n🔍 Buscando Juin + López:")
        parejas_juin = conn.execute(text("""
            SELECT tp.id, tp.categoria_id, tc.nombre as categoria,
                   u1.id_usuario, p1.nombre, p1.apellido,
                   u2.id_usuario, p2.nombre, p2.apellido,
                   tp.disponibilidad_horaria
            FROM torneos_parejas tp
            JOIN torneo_categorias tc ON tp.categoria_id = tc.id
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            LEFT JOIN perfil_usuarios p1 ON u1.id_usuario = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON u2.id_usuario = p2.id_usuario
            WHERE tp.torneo_id = 46 AND tc.nombre = '7ma'
              AND (
                (LOWER(p1.apellido) LIKE '%juin%' OR LOWER(p2.apellido) LIKE '%juin%')
                OR (LOWER(p1.apellido) LIKE '%lopez%' OR LOWER(p2.apellido) LIKE '%lopez%')
              )
        """)).fetchall()
        
        for p in parejas_juin:
            print(f"  🎾 Pareja ID {p[0]} - {p[2]}")
            print(f"     J1: ID {p[3]} - {p[4]} {p[5]}")
            print(f"     J2: ID {p[6]} - {p[7]} {p[8]}")
            if p[9]:
                print(f"     Restricciones: {p[9]}")
            else:
                print(f"     Sin restricciones")
        
        # Buscar Apostolo + Roldán
        print("\n🔍 Buscando Apostolo + Roldán:")
        parejas_apostolo = conn.execute(text("""
            SELECT tp.id, tp.categoria_id, tc.nombre as categoria,
                   u1.id_usuario, p1.nombre, p1.apellido,
                   u2.id_usuario, p2.nombre, p2.apellido,
                   tp.disponibilidad_horaria
            FROM torneos_parejas tp
            JOIN torneo_categorias tc ON tp.categoria_id = tc.id
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            LEFT JOIN perfil_usuarios p1 ON u1.id_usuario = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON u2.id_usuario = p2.id_usuario
            WHERE tp.torneo_id = 46 AND tc.nombre = '7ma'
              AND (
                (LOWER(p1.apellido) LIKE '%apostolo%' OR LOWER(p2.apellido) LIKE '%apostolo%')
                OR (LOWER(p1.apellido) LIKE '%roldan%' OR LOWER(p2.apellido) LIKE '%roldan%')
              )
        """)).fetchall()
        
        for p in parejas_apostolo:
            print(f"  🎾 Pareja ID {p[0]} - {p[2]}")
            print(f"     J1: ID {p[3]} - {p[4]} {p[5]}")
            print(f"     J2: ID {p[6]} - {p[7]} {p[8]}")
            if p[9]:
                print(f"     Restricciones: {p[9]}")
            else:
                print(f"     Sin restricciones")

if __name__ == "__main__":
    main()
