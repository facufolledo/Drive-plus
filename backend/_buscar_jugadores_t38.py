import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=e)()

buscar = [
    "fmontivero257",  # Montivero Federico
    "millicay",       # Millicay Gustavo
    "vera",           # Vera Jeremías
    "giordano",       # Giordano Matías
    "tapia",          # Tapia Damian
    "farran",         # Farran Bastian
    "vega",           # Vega Maxi
    "lobos",          # Lobos Javier
    "speziale",       # Speziale Tomas
    "alegre",         # Alegre Franco
]

for term in buscar:
    rows = s.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating,
               p.nombre, p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE LOWER(u.nombre_usuario) LIKE :t 
           OR LOWER(u.email) LIKE :t
           OR LOWER(p.apellido) LIKE :t2
    """), {"t": f"%{term.lower()}%", "t2": f"%{term.lower()}%"}).fetchall()
    
    if rows:
        for r in rows:
            print(f"  [{term}] ID:{r[0]} user:{r[1]} email:{r[2]} rating:{r[3]} nombre:{r[4]} {r[5]}")
    else:
        print(f"  [{term}] NO ENCONTRADO")

s.close()
