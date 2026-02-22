import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Parejas donde está 547 o 548
    print("Parejas con 547:")
    rows = c.execute(text("SELECT * FROM torneos_parejas WHERE jugador1_id = 547 OR jugador2_id = 547")).fetchall()
    for r in rows: print(f"  {r}")
    
    print("\nParejas con 548:")
    rows = c.execute(text("SELECT id, torneo_id, categoria_id, jugador1_id, jugador2_id FROM torneos_parejas WHERE jugador1_id = 548 OR jugador2_id = 548")).fetchall()
    for r in rows: print(f"  {r}")
    
    print("\nHistorial 547:")
    rows = c.execute(text("SELECT * FROM historial_rating WHERE id_usuario = 547")).fetchall()
    for r in rows: print(f"  {r}")
    
    print("\nHistorial 548:")
    rows = c.execute(text("SELECT * FROM historial_rating WHERE id_usuario = 548")).fetchall()
    for r in rows: print(f"  {r}")
