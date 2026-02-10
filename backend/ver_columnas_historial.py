from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv('backend/.env')
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'historial_rating' ORDER BY ordinal_position"))
    print("Columnas de historial_rating:")
    for row in result:
        print(f"  - {row[0]}")
