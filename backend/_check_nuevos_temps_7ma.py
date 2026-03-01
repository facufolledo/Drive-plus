"""Verificar qué usuarios se crearon nuevos en la inscripción de 7ma"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("=== Usuarios IDs 594-601 ===")
    result = conn.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email, u.rating, u.id_categoria
        FROM usuarios u
        JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.id_usuario IN (594, 595, 596, 597, 598, 599, 600, 601)
        ORDER BY u.id_usuario
    """))
    
    for r in result:
        tipo = "TEMP T42" if "@temp.com" in r[3] else "TEMP T38" if "@driveplus.temp" in r[3] else "REAL"
        print(f"  {r[0]}: {r[1]} {r[2]} - {tipo} - Rating:{r[4]} Cat:{r[5]}")
