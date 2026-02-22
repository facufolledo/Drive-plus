import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    for uid, nombre in [(562, "Juan Magi"), (564, "Flavio Palacio")]:
        print(f"\n=== {nombre} (ID {uid}) ===")
        u = c.execute(text("SELECT id_usuario, email, rating, id_categoria FROM usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
        print(f"  Usuario: {u}")
        
        parejas = c.execute(text("SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE jugador1_id = :id OR jugador2_id = :id"), {"id": uid}).fetchall()
        print(f"  Parejas: {len(parejas)}")
        for p in parejas:
            print(f"    Pareja {p[0]}: j1={p[1]} j2={p[2]}")
        
        hist = c.execute(text("SELECT id_historial, id_partido, rating_antes, delta, rating_despues FROM historial_rating WHERE id_usuario = :id"), {"id": uid}).fetchall()
        print(f"  Historial: {len(hist)}")
        for h in hist:
            print(f"    H{h[0]}: P{h[1]} | {h[2]} → {h[4]} (delta {h[3]})")
    
    # Verificar que temps ya no existen
    print("\n=== TEMPS ELIMINADOS ===")
    for tid in [511, 542]:
        r = c.execute(text("SELECT id_usuario FROM usuarios WHERE id_usuario = :id"), {"id": tid}).fetchone()
        print(f"  Temp {tid}: {'EXISTE ❌' if r else 'Eliminado ✅'}")
