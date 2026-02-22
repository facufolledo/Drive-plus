"""Ver bracket actual de 4ta T38."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Columnas de torneo_zonas
    cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='torneo_zonas' ORDER BY ordinal_position")).fetchall()
    print("Columnas torneo_zonas:", [col[0] for col in cols])
    
    # Zonas de 4ta - buscar por partidos de zona
    print("\n=== ZONAS 4ta (cat 87) ===")
    zonas = c.execute(text("""
        SELECT DISTINCT p.zona_id, tz.nombre, tz.numero_orden
        FROM partidos p
        JOIN torneo_zonas tz ON p.zona_id = tz.id
        WHERE p.id_torneo = 38 AND p.categoria_id = 87 AND p.fase = 'zona'
        ORDER BY tz.numero_orden
    """)).fetchall()
    for z in zonas:
        print(f"  Zona {z[1]} (ID {z[0]}, orden {z[2]})")
    print(f"\nTotal zonas: {len(zonas)}")
    
    # Bracket actual
    print("\n=== BRACKET 4ta T38 ===")
    partidos = c.execute(text("""
        SELECT p.id_partido, p.fase, p.numero_partido, p.pareja1_id, p.pareja2_id, 
               p.ganador_pareja_id, p.estado
        FROM partidos p
        WHERE p.id_torneo = 38 AND p.categoria_id = 87
        AND p.fase IN ('16avos', '8vos', '4tos', 'semis', 'final')
        ORDER BY 
            CASE p.fase 
                WHEN '16avos' THEN 1 WHEN '8vos' THEN 2 
                WHEN '4tos' THEN 3 WHEN 'semis' THEN 4 WHEN 'final' THEN 5 
            END,
            p.numero_partido
    """)).fetchall()
    
    for p in partidos:
        pid, fase, num, p1, p2, gan, estado = p
        names = []
        for pid_p in [p1, p2]:
            if pid_p:
                r = c.execute(text("""
                    SELECT pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
                    FROM torneos_parejas tp
                    JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
                    JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
                    WHERE tp.id = :pid
                """), {"pid": pid_p}).fetchone()
                names.append(r[0][:35] if r else f"?{pid_p}")
            else:
                names.append("---")
        
        print(f"  P{pid} | {fase} #{num} | {estado:10} | p1={p1} ({names[0]}) vs p2={p2} ({names[1]})")
    
    print(f"\nTotal partidos playoff: {len(partidos)}")
