"""
Script para actualizar el logo/imagen de un circuito.
Uso: python actualizar_logo_circuito.py <codigo> <url_imagen>
Ejemplo: python actualizar_logo_circuito.py zf https://ejemplo.com/foto.jpg
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

if len(sys.argv) < 3:
    print("Uso: python actualizar_logo_circuito.py <codigo> <url_imagen>")
    print("Ejemplo: python actualizar_logo_circuito.py zf https://ejemplo.com/foto.jpg")
    sys.exit(1)

codigo = sys.argv[1]
url = sys.argv[2]

with engine.connect() as conn:
    result = conn.execute(
        text("UPDATE circuitos SET logo_url = :url WHERE codigo = :codigo RETURNING id, nombre, logo_url"),
        {"url": url, "codigo": codigo}
    )
    row = result.fetchone()
    conn.commit()
    
    if row:
        print(f"✅ Circuito '{row[1]}' (id={row[0]}) actualizado con imagen: {row[2]}")
    else:
        print(f"❌ No se encontró circuito con código '{codigo}'")
