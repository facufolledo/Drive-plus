import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    print("Columnas de partidos:")
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'partidos' ORDER BY ordinal_position"))
    for row in result:
        print(f"  - {row[0]}")
