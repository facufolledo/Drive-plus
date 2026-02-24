"""Corregir partido Algarrilla/Millicay vs Martinez/Salomón - cambiar ganador"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# Parejas: 656 = Algarrilla/Millicay, 660 = Martinez/Salomón
with engine.connect() as conn:
    # Buscar el partido entre estas dos parejas
    partidos = conn.execute(text("""
        SELECT id_partido, fase, estado, pareja1_id, pareja2_id, resultado_padel,
               numero_partido, ganador_pareja_id, ganador_equipo
        FROM partidos
        WHERE id_torneo = 38 AND fase != 'zona'
          AND ((pareja1_id = 656 AND pareja2_id = 660) OR (pareja1_id = 660 AND pareja2_id = 656))
    """)).fetchall()
    
    print("=== PARTIDO ENCONTRADO ===")
    for p in partidos:
        print(f"  P{p[0]}: fase={p[1]} estado={p[2]} pa1={p[3]} pa2={p[4]} num={p[6]}")
        print(f"    ganador_pareja_id={p[7]}, ganador_equipo={p[8]}")
        print(f"    resultado_padel={p[5]}")
    
    if not partidos:
        # Buscar todos los partidos de playoff de pareja 656
        print("\nBuscando todos los partidos de playoff de pareja 656...")
        pts = conn.execute(text("""
            SELECT id_partido, fase, estado, pareja1_id, pareja2_id, resultado_padel,
                   numero_partido, ganador_pareja_id, ganador_equipo
            FROM partidos
            WHERE id_torneo = 38 AND fase != 'zona'
              AND (pareja1_id = 656 OR pareja2_id = 656)
            ORDER BY id_partido
        """)).fetchall()
        for p in pts:
            print(f"  P{p[0]}: fase={p[1]} estado={p[2]} pa1={p[3]} pa2={p[4]} num={p[6]}")
            print(f"    ganador_pareja_id={p[7]}, ganador_equipo={p[8]}")
            print(f"    resultado_padel={p[5]}")
        
        print("\nBuscando todos los partidos de playoff de pareja 660...")
        pts2 = conn.execute(text("""
            SELECT id_partido, fase, estado, pareja1_id, pareja2_id, resultado_padel,
                   numero_partido, ganador_pareja_id, ganador_equipo
            FROM partidos
            WHERE id_torneo = 38 AND fase != 'zona'
              AND (pareja1_id = 660 OR pareja2_id = 660)
            ORDER BY id_partido
        """)).fetchall()
        for p in pts2:
            print(f"  P{p[0]}: fase={p[1]} estado={p[2]} pa1={p[3]} pa2={p[4]} num={p[6]}")
            print(f"    ganador_pareja_id={p[7]}, ganador_equipo={p[8]}")
            print(f"    resultado_padel={p[5]}")
