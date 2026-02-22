"""Fix: Pablo Ferreyra y Carlos Gudiño son de 4ta, no de 8va.
El temp era de 4ta con rating 1299 (incorrecto), el real tenía 1699.
Restaurar rating original."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Restaurar ratings originales
    c.execute(text("UPDATE usuarios SET rating = 1699 WHERE id_usuario = 84"))  # Pablo Ferreyra
    c.execute(text("UPDATE usuarios SET rating = 1699 WHERE id_usuario = 67"))  # Carlos Gudiño
    print("Pablo Ferreyra (84): rating restaurado a 1699")
    print("Carlos Gudiño (67): rating restaurado a 1699")
    c.commit()
