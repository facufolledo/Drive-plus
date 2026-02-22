import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as c:
    cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='usuarios' ORDER BY ordinal_position")).fetchall()
    for col in cols:
        print(col[0])
    
    # Verificar estado actual de Magi temp 511
    print("\n--- Estado temp 511 ---")
    r = c.execute(text("SELECT id_usuario, email FROM usuarios WHERE id_usuario = 511")).fetchone()
    print(f"Existe: {r}")
    
    # Verificar parejas de real 562
    print("\n--- Parejas de real 562 ---")
    rows = c.execute(text("SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE jugador1_id = 562 OR jugador2_id = 562")).fetchall()
    for r in rows:
        print(f"  Pareja {r[0]}: j1={r[1]} j2={r[2]}")
    
    # Verificar historial de real 562
    h = c.execute(text("SELECT COUNT(*) FROM historial_rating WHERE id_usuario = 562")).scalar()
    print(f"\nHistorial real 562: {h}")
    h2 = c.execute(text("SELECT COUNT(*) FROM historial_rating WHERE id_usuario = 511")).scalar()
    print(f"Historial temp 511: {h2}")
