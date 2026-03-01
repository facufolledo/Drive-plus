"""Buscar todos los Martin Navarro"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("=== BUSCANDO MARTIN NAVARRO ===\n")
    
    result = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.partidos_jugados,
               p.nombre, p.apellido
        FROM usuarios u
        JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE (LOWER(p.nombre) LIKE '%martin%' AND LOWER(p.apellido) LIKE '%navarro%')
           OR (LOWER(p.nombre) LIKE '%navarro%' AND LOWER(p.apellido) LIKE '%martin%')
        ORDER BY u.id_usuario
    """)).fetchall()
    
    if result:
        for r in result:
            tipo = "TEMP" if "temp" in r[2].lower() else "REAL"
            print(f"ID {r[0]}: {r[5]} {r[6]}")
            print(f"  User: {r[1]}")
            print(f"  Email: {r[2]} ({tipo})")
            print(f"  Rating: {r[3]}, Partidos: {r[4]}")
            
            # Verificar parejas
            parejas = conn.execute(text("""
                SELECT tp.id, tp.torneo_id, tp.categoria_id
                FROM torneos_parejas tp
                WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
            """), {"uid": r[0]}).fetchall()
            
            if parejas:
                print(f"  Parejas ({len(parejas)}):")
                for p in parejas:
                    print(f"    - Pareja {p[0]} en T{p[1]} Cat{p[2]}")
            else:
                print(f"  Sin parejas")
            print()
    else:
        print("No se encontró ningún Martin Navarro")
