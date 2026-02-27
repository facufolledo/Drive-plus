"""Buscar jugadores para inscribir en 5ta T42"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

jugadores = [
    "Calderón Juan", "Villegas Ignacio",
    "Oliva Bautista", "Peñaloza Nicolás",
    "Romero Isaías", "Romero Martín",
    "Castro Joel", "Aguilar Gonzalo",
    "Brizuela Joaquín", "Casas Miguel",
    "Nieto Axel", "Tello Sergio",
    "Díaz Mateo", "Sosa Bautista",
    "Nani Tomás", "Abrego Maxi",
    "Loto Juan", "Navarro Martín",
    "Farran Bastian", "Montiel Tomás",
    "Ruarte Leandro", "Romero Gastón",
]

with engine.connect() as conn:
    for nombre_completo in jugadores:
        partes = nombre_completo.split()
        # Buscar por apellido (primera palabra) y nombre
        apellido = partes[0]
        nombre = partes[1] if len(partes) > 1 else ''
        
        results = conn.execute(text("""
            SELECT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria,
                   u.nombre_usuario
            FROM usuarios u
            JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
            WHERE (LOWER(p.apellido) LIKE :ap AND LOWER(p.nombre) LIKE :nom)
               OR (LOWER(p.nombre) LIKE :ap AND LOWER(p.apellido) LIKE :nom)
            ORDER BY u.id_usuario
        """), {"ap": f"%{apellido.lower()}%", "nom": f"%{nombre.lower()}%"}).fetchall()
        
        if results:
            for r in results:
                print(f"  ✅ {nombre_completo} -> ID:{r[0]} {r[1]} {r[2]} (user:{r[5]}) rating:{r[3]} cat:{r[4]}")
        else:
            print(f"  ❌ {nombre_completo} -> NO ENCONTRADO")
