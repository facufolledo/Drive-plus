import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
s = sessionmaker(bind=e)()
r = s.execute(text("SELECT id, nombre FROM torneos WHERE nombre LIKE '%Demo%' OR nombre LIKE '%demo%'")).fetchall()
for row in r:
    print(f"ID: {row[0]} - {row[1]}")
if not r:
    print("No hay torneos demo")
# Contar usuarios demo
r2 = s.execute(text("SELECT COUNT(*) FROM usuarios WHERE email LIKE 'demo%@demo.com'")).fetchone()
print(f"Usuarios demo: {r2[0]}")
s.close()
