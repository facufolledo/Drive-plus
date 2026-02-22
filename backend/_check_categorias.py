import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'categorias' ORDER BY ordinal_position")).fetchall()
    print("Columnas:", [r[0] for r in cols])
    pk = cols[0][0]
    rows = c.execute(text(f"SELECT * FROM categorias ORDER BY {pk}")).fetchall()
    for r in rows:
        print(r)
