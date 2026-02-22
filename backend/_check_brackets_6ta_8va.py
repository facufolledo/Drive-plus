"""Ver brackets actuales de 6ta y 8va T38."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    for cat_id, cat_name in [(88, "6ta"), (89, "8va")]:
        print(f"\n{'='*60}")
        print(f"=== {cat_name} (cat {cat_id}) ===")
        print(f"{'='*60}")
        
        # Zonas
        zonas = c.execute(text("""
            SELECT DISTINCT p.zona_id, tz.nombre
            FROM partidos p
            JOIN torneo_zonas tz ON p.zona_id = tz.id
            WHERE p.id_torneo = 38 AND p.categoria_id = :cat AND p.fase = 'zona'
            ORDER BY tz.nombre
        """), {"cat": cat_id}).fetchall()
        print(f"Zonas: {len(zonas)} - {[z[1] for z in zonas]}")
        
        # Playoffs
        partidos = c.execute(text("""
            SELECT p.id_partido, p.fase, p.numero_partido, p.pareja1_id, p.pareja2_id, p.estado, p.ganador_pareja_id
            FROM partidos p
            WHERE p.id_torneo = 38 AND p.categoria_id = :cat
            AND p.fase IN ('8vos', '4tos', 'semis', 'final')
            ORDER BY 
                CASE p.fase WHEN '8vos' THEN 1 WHEN '4tos' THEN 2 WHEN 'semis' THEN 3 WHEN 'final' THEN 4 END,
                p.numero_partido
        """), {"cat": cat_id}).fetchall()
        
        if not partidos:
            print("  Sin playoffs generados")
            continue
            
        con_resultado = sum(1 for p in partidos if p[5] == 'confirmado')
        print(f"Playoffs: {len(partidos)} partidos ({con_resultado} con resultado)")
        
        for p in partidos:
            pid, fase, num, p1, p2, estado, gan = p
            print(f"  P{pid} | {fase} #{num} | {estado:10} | p1={p1} p2={p2} | gan={gan}")
