"""Migrar historial de rating de temp 502 a real 568"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Ver columnas de historial_rating
    cols = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'historial_rating' ORDER BY ordinal_position
    """)).fetchall()
    print("Columnas historial_rating:", [c[0] for c in cols])
    
    # Buscar historial del temp 502
    id_col = cols[1][0] if len(cols) > 1 else 'id_usuario'  # probable nombre
    print(f"\nBuscando historial con columna de usuario...")
    
    # Intentar con id_usuario
    try:
        h = conn.execute(text("SELECT COUNT(*) FROM historial_rating WHERE id_usuario = :tid"), {"tid": 502}).scalar()
        print(f"Historial temp 502 (id_usuario): {h} registros")
        
        if h > 0:
            conn.execute(text("UPDATE historial_rating SET id_usuario = :real WHERE id_usuario = :temp"), {"real": 568, "temp": 502})
            conn.commit()
            print(f"✅ Historial migrado: {h} registros de 502 -> 568")
        else:
            print("Sin historial para migrar")
    except Exception as e:
        print(f"Error con id_usuario: {e}")
    
    # Verificar estado final
    print("\n=== VERIFICACIÓN FINAL ===")
    real = conn.execute(text(
        "SELECT id_usuario, nombre_usuario, rating, id_categoria FROM usuarios WHERE id_usuario = 568"
    )).fetchone()
    print(f"Real 568: user={real[1]}, rating={real[2]}, cat={real[3]}")
    
    pareja = conn.execute(text(
        "SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = 631"
    )).fetchone()
    print(f"Pareja 631: j1={pareja[1]}, j2={pareja[2]}")
    
    partidos = conn.execute(text("""
        SELECT id_partido, fase, estado, pareja1_id, pareja2_id
        FROM partidos WHERE pareja1_id = 631 OR pareja2_id = 631
        ORDER BY id_partido
    """)).fetchall()
    print(f"Partidos pareja 631 ({len(partidos)}):")
    for p in partidos:
        print(f"  P{p[0]}: fase={p[1]} estado={p[2]} pa1={p[3]} pa2={p[4]}")
