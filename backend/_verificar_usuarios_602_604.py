"""Verificar si usuarios 602-604 necesitan migración"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

usuarios_verificar = [
    (602, "martinnavarro20166", "martinnavarro20166@gmail.com"),
    (603, "aeaz.loto.emilio", "aeaz.loto.emilio@gmail.com"),
    (604, "saavedrahector4747", "saavedrahector4747@gmail.com"),
]

with engine.connect() as conn:
    print("=== VERIFICACIÓN USUARIOS 602-604 ===\n")
    
    for uid, username, email in usuarios_verificar:
        print(f"\n--- Usuario {uid}: {username} ---")
        
        # Verificar si existe
        usuario = conn.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.partidos_jugados,
                   p.nombre, p.apellido
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE u.id_usuario = :uid
        """), {"uid": uid}).fetchone()
        
        if not usuario:
            print(f"  ❌ Usuario {uid} NO EXISTE")
            continue
        
        print(f"  Email: {usuario[2]}")
        print(f"  Nombre: {usuario[5]} {usuario[6]}")
        print(f"  Rating: {usuario[3]}, Partidos: {usuario[4]}")
        
        # Buscar duplicados por nombre
        if usuario[5] and usuario[6]:
            duplicados = conn.execute(text("""
                SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.partidos_jugados
                FROM usuarios u
                JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
                WHERE LOWER(p.nombre) = LOWER(:nombre)
                AND LOWER(p.apellido) = LOWER(:apellido)
                AND u.id_usuario != :uid
            """), {"nombre": usuario[5], "apellido": usuario[6], "uid": uid}).fetchall()
            
            if duplicados:
                print(f"\n  ⚠️ DUPLICADOS ENCONTRADOS ({len(duplicados)}):")
                for dup in duplicados:
                    tipo = "TEMP" if "temp" in dup[2].lower() else "REAL"
                    print(f"    - ID {dup[0]}: {dup[1]} ({dup[2]}) - {tipo} - Rating:{dup[3]} PJ:{dup[4]}")
            else:
                print(f"\n  ✅ No hay duplicados")
        
        # Verificar parejas
        parejas = conn.execute(text("""
            SELECT tp.id, tp.torneo_id, tp.categoria_id
            FROM torneos_parejas tp
            WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
        """), {"uid": uid}).fetchall()
        
        if parejas:
            print(f"\n  Parejas inscritas ({len(parejas)}):")
            for p in parejas:
                print(f"    - Pareja {p[0]} en T{p[1]} Cat{p[2]}")
        else:
            print(f"\n  Sin parejas inscritas")
    
    print("\n\n✅ Verificación completada")
