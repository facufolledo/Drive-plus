"""
Migrar Benjamin Hrellac: temp 502 -> real 568
- Pareja 631 (j1=50, j2=502) en T38 6ta -> cambiar j2 a 568
- Copiar rating 1363 y cat 3 del temp al real
- No tocar el temp (ya jugó partidos en torneos anteriores potencialmente)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

TEMP_ID = 502
REAL_ID = 568

with engine.connect() as conn:
    # Verificar estado actual
    print("=== ANTES ===")
    
    real = conn.execute(text(
        "SELECT id_usuario, nombre_usuario, rating, id_categoria FROM usuarios WHERE id_usuario = :id"
    ), {"id": REAL_ID}).fetchone()
    print(f"Real {REAL_ID}: user={real[1]}, rating={real[2]}, cat={real[3]}")
    
    temp = conn.execute(text(
        "SELECT id_usuario, nombre_usuario, rating, id_categoria FROM usuarios WHERE id_usuario = :id"
    ), {"id": TEMP_ID}).fetchone()
    print(f"Temp {TEMP_ID}: user={temp[1]}, rating={temp[2]}, cat={temp[3]}")
    
    pareja = conn.execute(text(
        "SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = 631"
    )).fetchone()
    print(f"Pareja 631: j1={pareja[1]}, j2={pareja[2]}")
    
    # 1. Actualizar rating y categoría del real con los del temp
    conn.execute(text("""
        UPDATE usuarios SET rating = :rating, id_categoria = :cat
        WHERE id_usuario = :real_id
    """), {"rating": temp[2], "cat": temp[3], "real_id": REAL_ID})
    print(f"\n✅ Rating real actualizado: {real[2]} -> {temp[2]}, cat: {real[3]} -> {temp[3]}")
    
    # 2. Actualizar pareja 631: cambiar jugador2 de temp a real
    conn.execute(text("""
        UPDATE torneos_parejas SET jugador2_id = :real_id
        WHERE id = 631 AND jugador2_id = :temp_id
    """), {"real_id": REAL_ID, "temp_id": TEMP_ID})
    print(f"✅ Pareja 631: j2 cambiado de {TEMP_ID} -> {REAL_ID}")
    
    # 3. Migrar historial de rating del temp al real
    historial = conn.execute(text("""
        SELECT COUNT(*) FROM historial_rating WHERE usuario_id = :tid
    """), {"tid": TEMP_ID}).scalar()
    
    if historial > 0:
        conn.execute(text("""
            UPDATE historial_rating SET usuario_id = :real_id
            WHERE usuario_id = :temp_id
        """), {"real_id": REAL_ID, "temp_id": TEMP_ID})
        print(f"✅ Historial de rating migrado: {historial} registros")
    else:
        print("ℹ️ Sin historial de rating para migrar")
    
    conn.commit()
    
    # Verificar
    print("\n=== DESPUÉS ===")
    real2 = conn.execute(text(
        "SELECT id_usuario, nombre_usuario, rating, id_categoria FROM usuarios WHERE id_usuario = :id"
    ), {"id": REAL_ID}).fetchone()
    print(f"Real {REAL_ID}: user={real2[1]}, rating={real2[2]}, cat={real2[3]}")
    
    pareja2 = conn.execute(text(
        "SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = 631"
    )).fetchone()
    print(f"Pareja 631: j1={pareja2[1]}, j2={pareja2[2]}")
    
    partidos = conn.execute(text("""
        SELECT id_partido, fase, estado, pareja1_id, pareja2_id
        FROM partidos
        WHERE pareja1_id = 631 OR pareja2_id = 631
        ORDER BY id_partido
    """)).fetchall()
    print(f"Partidos de pareja 631 ({len(partidos)}):")
    for p in partidos:
        print(f"  P{p[0]}: fase={p[1]} estado={p[2]} pa1={p[3]} pa2={p[4]}")
