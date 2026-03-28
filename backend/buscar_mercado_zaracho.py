"""
Buscar pareja Mercado + Zaracho en torneo 46
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
    print("BUSCANDO MERCADO + ZARACHO EN TORNEO 46")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Buscar usuarios Mercado
        mercados = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.apellido) LIKE '%mercado%' OR LOWER(u.nombre_usuario) LIKE '%mercado%'
            ORDER BY u.id_usuario
        """)).fetchall()
        
        print("\n📋 USUARIOS MERCADO:")
        for m in mercados:
            print(f"  ID {m[0]} - {m[2]} {m[3]} (@{m[1]})")
        
        # Buscar usuarios Zaracho
        zarachos = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.apellido) LIKE '%zaracho%' OR LOWER(u.nombre_usuario) LIKE '%zaracho%'
            ORDER BY u.id_usuario
        """)).fetchall()
        
        print("\n📋 USUARIOS ZARACHO:")
        for z in zarachos:
            print(f"  ID {z[0]} - {z[2]} {z[3]} (@{z[1]})")
        
        # Buscar parejas en torneo 46
        print("\n" + "=" * 80)
        print("PAREJAS EN TORNEO 46 CON MERCADO O ZARACHO")
        print("=" * 80)
        
        parejas = conn.execute(text("""
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
            WHERE tp.torneo_id = 46
              AND (
                LOWER(p1.apellido) LIKE '%mercado%' OR LOWER(p2.apellido) LIKE '%mercado%'
                OR LOWER(p1.apellido) LIKE '%zaracho%' OR LOWER(p2.apellido) LIKE '%zaracho%'
              )
            ORDER BY tp.id
        """)).fetchall()
        
        if not parejas:
            print("❌ No se encontraron parejas con Mercado o Zaracho en torneo 46")
            return
        
        for p in parejas:
            print(f"\n🎾 Pareja ID {p[0]} - Categoría: {p[2]}")
            print(f"   J1: ID {p[3]} - {p[4]} {p[5]}")
            print(f"   J2: ID {p[6]} - {p[7]} {p[8]}")
            if p[9]:
                print(f"   Restricciones actuales: {p[9]}")
            else:
                print(f"   Sin restricciones")

if __name__ == "__main__":
    main()
