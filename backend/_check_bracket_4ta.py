"""Ver bracket actual de 4ta T38."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Zonas de 4ta
    print("=== ZONAS 4ta (cat 87) ===")
    zonas = c.execute(text("""
        SELECT tz.id, tz.nombre, tz.numero_orden
        FROM torneo_zonas tz
        WHERE tz.torneo_categoria_id = 87
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
        # Get names
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
                names.append(r[0] if r else f"?{pid_p}")
            else:
                names.append("---")
        
        print(f"  P{p[0]} | {fase} #{num} | {estado} | p1={p1} ({names[0][:30]}) vs p2={p2} ({names[1][:30]})")
    
    print(f"\nTotal partidos playoff: {len(partidos)}")
    
    # Clasificados por zona
    print("\n=== CLASIFICADOS POR ZONA ===")
    for z in zonas:
        clas = c.execute(text("""
            SELECT czp.posicion, czp.pareja_id, czp.puntos,
                   pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
            FROM clasificacion_zona_parejas czp
            JOIN torneos_parejas tp ON czp.pareja_id = tp.id
            JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
            JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
            WHERE czp.zona_id = :zid
            ORDER BY czp.posicion
            LIMIT 2
        """), {"zid": z[0]}).fetchall()
        print(f"\n  Zona {z[1]}:")
        for cl in clas:
            print(f"    {cl[0]}° - Pareja {cl[1]} ({cl[3][:35]}) - {cl[2]} pts")
