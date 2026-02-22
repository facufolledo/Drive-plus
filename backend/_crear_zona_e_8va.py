"""Crear zona E en 8va (cat 89) del T38 con 2 parejas nuevas + 1 partido.
Pareja 1: Agustin Martinez (en app) + Sofia Salomon (en app)
Pareja 2: Tiago Cordoba (en app, ID 195) + Camilo Nieto (temp nuevo, NO el que ya está)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # 1. Buscar jugadores existentes
    print("=" * 60)
    print("BUSCAR JUGADORES")
    print("=" * 60)
    
    # Agustin Martinez - hay un temp (ID 170) de Principiante, buscar el real
    for search in ['martinez', 'agustin']:
        rows = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido, u.rating
            FROM usuarios u JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE (LOWER(p.nombre) LIKE :s OR LOWER(p.apellido) LIKE :s)
            AND u.email NOT LIKE '%@driveplus.temp'
            ORDER BY u.id_usuario
        """), {"s": f"%{search}%"}).fetchall()
        print(f"\n  Buscar '{search}' (reales):")
        for r in rows:
            print(f"    ID {r[0]}: {r[3]} {r[4]} ({r[1]}, {r[2]}, rating={r[5]})")

    # Sofia Salomon
    for search in ['salomon', 'sofia']:
        rows = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido, u.rating
            FROM usuarios u JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE (LOWER(p.nombre) LIKE :s OR LOWER(p.apellido) LIKE :s)
            ORDER BY u.id_usuario
        """), {"s": f"%{search}%"}).fetchall()
        print(f"\n  Buscar '{search}':")
        for r in rows:
            print(f"    ID {r[0]}: {r[3]} {r[4]} ({r[1]}, {r[2]}, rating={r[5]})")

    # Tiago Cordoba
    for search in ['tiago', 'cordoba']:
        rows = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido, u.rating
            FROM usuarios u JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE (LOWER(p.nombre) LIKE :s OR LOWER(p.apellido) LIKE :s)
            ORDER BY u.id_usuario
        """), {"s": f"%{search}%"}).fetchall()
        print(f"\n  Buscar '{search}':")
        for r in rows:
            print(f"    ID {r[0]}: {r[3]} {r[4]} ({r[1]}, {r[2]}, rating={r[5]})")

    # Camilo Nieto
    for search in ['nieto', 'camilo']:
        rows = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido, u.rating
            FROM usuarios u JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE (LOWER(p.nombre) LIKE :s OR LOWER(p.apellido) LIKE :s)
            ORDER BY u.id_usuario
        """), {"s": f"%{search}%"}).fetchall()
        print(f"\n  Buscar '{search}':")
        for r in rows:
            print(f"    ID {r[0]}: {r[3]} {r[4]} ({r[1]}, {r[2]}, rating={r[5]})")

    # Zonas actuales de 8va
    print(f"\n{'=' * 60}")
    print("ZONAS ACTUALES 8VA (cat 89)")
    print("=" * 60)
    zonas = c.execute(text("""
        SELECT id, nombre, numero_orden FROM torneo_zonas 
        WHERE torneo_id = 38 AND categoria_id = 89 ORDER BY numero_orden
    """)).fetchall()
    for z in zonas:
        print(f"  Zona {z[1]} (ID {z[0]}, orden {z[2]})")
