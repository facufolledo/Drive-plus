"""Verificar categoría de Martin Navarro"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT u.id_usuario, u.email, u.rating, u.id_categoria, c.nombre
        FROM usuarios u
        JOIN categorias c ON u.id_categoria = c.id_categoria
        WHERE u.id_usuario = 602
    """)).fetchone()
    
    print(f"Usuario {result[0]}: {result[1]}")
    print(f"Rating: {result[2]}")
    print(f"Categoría: {result[4]} (ID {result[3]})")
    print(f"\n✅ Correcto: Rating 1499 debe estar en 5ta (1400-1599)")
