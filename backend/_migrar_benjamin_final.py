"""Migrar Benjamin Hrellac: temp 502 -> real 568 (todo en uno)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

TEMP_ID = 502
REAL_ID = 568

with engine.connect() as conn:
    print("=== ANTES ===")
    real = conn.execute(text("SELECT id_usuario, rating, id_categoria FROM usuarios WHERE id_usuario = :id"), {"id": REAL_ID}).fetchone()
    temp = conn.execute(text("SELECT id_usuario, rating, id_categoria FROM usuarios WHERE id_usuario = :id"), {"id": TEMP_ID}).fetchone()
    print(f"Real {REAL_ID}: rating={real[1]}, cat={real[2]}")
    print(f"Temp {TEMP_ID}: rating={temp[1]}, cat={temp[2]}")
    
    pareja = conn.execute(text("SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = 631")).fetchone()
    print(f"Pareja 631: j1={pareja[1]}, j2={pareja[2]}")

    # 1. Copiar rating y categoría del temp al real
    conn.execute(text("""
        UPDATE usuarios SET rating = :rating, id_categoria = :cat WHERE id_usuario = :rid
    """), {"rating": temp[1], "cat": temp[2], "rid": REAL_ID})
    
    # 2. Cambiar jugador2 en pareja 631
    conn.execute(text("""
        UPDATE torneos_parejas SET jugador2_id = :rid WHERE id = 631 AND jugador2_id = :tid
    """), {"rid": REAL_ID, "tid": TEMP_ID})
    
    conn.commit()
    
    print("\n=== DESPUÉS ===")
    real2 = conn.execute(text("SELECT id_usuario, rating, id_categoria FROM usuarios WHERE id_usuario = :id"), {"id": REAL_ID}).fetchone()
    print(f"Real {REAL_ID}: rating={real2[1]}, cat={real2[2]}")
    
    pareja2 = conn.execute(text("SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = 631")).fetchone()
    print(f"Pareja 631: j1={pareja2[1]}, j2={pareja2[2]}")
    
    partidos = conn.execute(text("""
        SELECT id_partido, fase, estado FROM partidos 
        WHERE pareja1_id = 631 OR pareja2_id = 631 ORDER BY id_partido
    """)).fetchall()
    print(f"Partidos ({len(partidos)}):")
    for p in partidos:
        print(f"  P{p[0]}: {p[1]} - {p[2]}")
    
    print("\n✅ Migración completada: Benjamin Hrellac temp 502 -> real 568")
