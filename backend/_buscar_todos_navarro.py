"""Buscar todos los apellidos Navarro"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("=== TODOS LOS NAVARRO ===\n")
    
    result = conn.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email, u.rating, u.partidos_jugados
        FROM usuarios u
        JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE LOWER(p.apellido) LIKE '%navarro%'
        ORDER BY u.id_usuario
    """)).fetchall()
    
    for r in result:
        tipo = "TEMP" if "temp" in r[3].lower() else "REAL"
        print(f"{r[0]}: {r[1]} {r[2]} - {tipo} - R:{r[4]} PJ:{r[5]}")
