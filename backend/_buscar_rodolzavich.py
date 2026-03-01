"""Buscar usuario Rodolzavich real"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("=== Buscando Rodolzavich ===")
    result = conn.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email, u.rating, u.id_categoria
        FROM usuarios u
        JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE LOWER(p.apellido) LIKE '%rodolza%' OR LOWER(p.apellido) LIKE '%rodoldo%'
        ORDER BY u.id_usuario
    """))
    
    usuarios = result.fetchall()
    if usuarios:
        for r in usuarios:
            tipo = "TEMP" if "temp" in r[3].lower() else "REAL"
            print(f"  {r[0]}: {r[1]} {r[2]} - {tipo} - {r[3]} - Rating:{r[4]} Cat:{r[5]}")
    else:
        print("  No se encontró ningún usuario con apellido similar")
