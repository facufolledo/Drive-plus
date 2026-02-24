"""Buscar partido Algarrilla/Millicay vs Salomón en playoffs T38"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Buscar parejas con Algarrilla, Millicay o Salomon
    print("=== BUSCANDO PAREJAS ===")
    parejas = conn.execute(text("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.torneo_id,
               p1.nombre || ' ' || p1.apellido as j1_nombre,
               p2.nombre || ' ' || p2.apellido as j2_nombre
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios p1 ON p1.id_usuario = tp.jugador1_id
        LEFT JOIN perfil_usuarios p2 ON p2.id_usuario = tp.jugador2_id
        WHERE tp.torneo_id = 38
          AND (
            LOWER(p1.apellido) LIKE '%algarr%' OR LOWER(p2.apellido) LIKE '%algarr%'
            OR LOWER(p1.apellido) LIKE '%millicay%' OR LOWER(p2.apellido) LIKE '%millicay%'
            OR LOWER(p1.apellido) LIKE '%salom%' OR LOWER(p2.apellido) LIKE '%salom%'
          )
    """)).fetchall()
    for p in parejas:
        print(f"  Pareja {p[0]}: {p[4]} / {p[5]} (j1={p[1]}, j2={p[2]}, torneo={p[3]})")

    # Buscar partidos de playoffs con estas parejas
    if parejas:
        pareja_ids = [p[0] for p in parejas]
        print(f"\nPareja IDs: {pareja_ids}")
        
        # Columnas de partidos
        cols = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'partidos' ORDER BY ordinal_position
        """)).fetchall()
        print(f"Columnas partidos: {[c[0] for c in cols]}")
        
        # Buscar partidos de playoff con estas parejas
        for pid in pareja_ids:
            partidos = conn.execute(text("""
                SELECT pt.id_partido, pt.fase, pt.estado, pt.pareja1_id, pt.pareja2_id,
                       pt.resultado, pt.numero_partido
                FROM partidos pt
                WHERE pt.id_torneo = 38 AND pt.fase != 'zona'
                  AND (pt.pareja1_id = :pid OR pt.pareja2_id = :pid)
                ORDER BY pt.id_partido
            """), {"pid": pid}).fetchall()
            for pt in partidos:
                print(f"\n  P{pt[0]}: fase={pt[1]} estado={pt[2]} pa1={pt[3]} pa2={pt[4]} num={pt[6]}")
                print(f"    resultado={pt[5]}")
