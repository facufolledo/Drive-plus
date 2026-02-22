import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as c:
    c.execute(text("UPDATE torneos_parejas SET estado = 'confirmada' WHERE id = 630"))
    c.commit()
    r = c.execute(text("SELECT id, estado FROM torneos_parejas WHERE id = 630")).fetchone()
    print(f"Pareja {r[0]} -> estado: {r[1]}")
