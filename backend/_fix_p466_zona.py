import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Check P466
    p = c.execute(text("SELECT id_partido, zona_id, categoria_id, pareja1_id, pareja2_id FROM partidos WHERE id_partido = 466")).fetchone()
    print(f"P466: zona_id={p[1]} cat={p[2]} p1={p[3]} p2={p[4]}")
    
    # Zona F = ID 209
    print(f"Zona F ID: 209")
    
    # Set zona_id
    c.execute(text("UPDATE partidos SET zona_id = 209 WHERE id_partido = 466"))
    c.commit()
    
    p2 = c.execute(text("SELECT zona_id FROM partidos WHERE id_partido = 466")).fetchone()
    print(f"P466 zona_id actualizado: {p2[0]}")
    
    # También verificar P465 (8va zona E) y P403 (4ta zona E)
    for pid in [465, 403]:
        p = c.execute(text("SELECT id_partido, zona_id FROM partidos WHERE id_partido = :pid"), {"pid": pid}).fetchone()
        print(f"P{pid}: zona_id={p[1]}")
