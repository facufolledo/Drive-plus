import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'usuarios' ORDER BY ordinal_position")).fetchall()
    for r in cols:
        print(r[0])
