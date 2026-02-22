"""Ver clasificados de 4ta por zona para entender los cruces APA."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    zonas = c.execute(text("""
        SELECT DISTINCT p.zona_id, tz.nombre, tz.numero_orden
        FROM partidos p
        JOIN torneo_zonas tz ON p.zona_id = tz.id
        WHERE p.id_torneo = 38 AND p.categoria_id = 87 AND p.fase = 'zona'
        ORDER BY tz.numero_orden
    """)).fetchall()
    
    for z in zonas:
        print(f"\n=== {z[1]} (ID {z[0]}) ===")
        clas = c.execute(text("""
            SELECT czp.posicion, czp.pareja_id, czp.puntos,
                   pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
            FROM clasificacion_zona_parejas czp
            JOIN torneos_parejas tp ON czp.pareja_id = tp.id
            JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
            JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
            WHERE czp.zona_id = :zid
            ORDER BY czp.posicion
        """), {"zid": z[0]}).fetchall()
        for cl in clas:
            print(f"  {cl[0]}° - Pareja {cl[1]} | {cl[3][:40]} | {cl[2]} pts")
    
    # Ahora mapear las parejas del bracket a sus zonas
    print("\n\n=== MAPEO BRACKET → ZONAS ===")
    bracket = c.execute(text("""
        SELECT p.id_partido, p.fase, p.numero_partido, p.pareja1_id, p.pareja2_id, p.estado
        FROM partidos p
        WHERE p.id_torneo = 38 AND p.categoria_id = 87
        AND p.fase = '8vos'
        ORDER BY p.numero_partido
    """)).fetchall()
    
    for b in bracket:
        pid, fase, num, p1, p2, estado = b
        for label, pid_p in [("p1", p1), ("p2", p2)]:
            if pid_p:
                zona_info = c.execute(text("""
                    SELECT tz.nombre, czp.posicion
                    FROM clasificacion_zona_parejas czp
                    JOIN torneo_zonas tz ON czp.zona_id = tz.id
                    WHERE czp.pareja_id = :pid
                    AND tz.id IN (SELECT DISTINCT zona_id FROM partidos WHERE id_torneo = 38 AND categoria_id = 87 AND fase = 'zona')
                """), {"pid": pid_p}).fetchone()
                nombre = c.execute(text("""
                    SELECT pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
                    FROM torneos_parejas tp
                    JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
                    JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
                    WHERE tp.id = :pid
                """), {"pid": pid_p}).fetchone()
                zona_str = f"{zona_info[0]} {zona_info[1]}°" if zona_info else "???"
                print(f"  8vos#{num} {label}: Pareja {pid_p} = {nombre[0][:30] if nombre else '?'} [{zona_str}]")
