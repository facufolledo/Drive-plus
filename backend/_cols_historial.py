import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    r = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='historial_rating' ORDER BY ordinal_position"))
    print("Columnas historial_rating:")
    for x in r:
        print(f"  {x[0]}")
