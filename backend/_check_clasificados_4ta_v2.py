"""Ver clasificados de 4ta por zona y mapear bracket."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Parejas por zona (usando torneos_zona_parejas)
    zonas = c.execute(text("""
        SELECT tz.id, tz.nombre, tz.numero_orden
        FROM torneo_zonas tz
        WHERE tz.torneo_id = 38 AND tz.categoria_id = 87
        ORDER BY tz.numero_orden
    """)).fetchall()
    
    pareja_zona_map = {}  # pareja_id -> (zona_nombre, posicion)
    
    for z in zonas:
        zid, zname, zord = z
        # Get parejas in this zone from partidos
        parejas_zona = c.execute(text("""
            SELECT DISTINCT tp_id FROM (
                SELECT pareja1_id as tp_id FROM partidos WHERE zona_id = :zid AND fase = 'zona' AND pareja1_id IS NOT NULL
                UNION
                SELECT pareja2_id as tp_id FROM partidos WHERE zona_id = :zid AND fase = 'zona' AND pareja2_id IS NOT NULL
            ) sub
        """), {"zid": zid}).fetchall()
        
        print(f"\n=== {zname} (ID {zid}) - {len(parejas_zona)} parejas ===")
        for pp in parejas_zona:
            pid = pp[0]
            nombre = c.execute(text("""
                SELECT pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
                FROM torneos_parejas tp
                JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
                JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
                WHERE tp.id = :pid
            """), {"pid": pid}).fetchone()
            print(f"  Pareja {pid}: {nombre[0][:40] if nombre else '?'}")
            pareja_zona_map[pid] = zname
    
    # Bracket 8vos
    print("\n\n=== BRACKET 8vos → ZONAS ===")
    bracket = c.execute(text("""
        SELECT p.id_partido, p.numero_partido, p.pareja1_id, p.pareja2_id, p.estado
        FROM partidos p
        WHERE p.id_torneo = 38 AND p.categoria_id = 87 AND p.fase = '8vos'
        ORDER BY p.numero_partido
    """)).fetchall()
    
    for b in bracket:
        pid, num, p1, p2, estado = b
        p1_zona = pareja_zona_map.get(p1, '---') if p1 else '---'
        p2_zona = pareja_zona_map.get(p2, '---') if p2 else '---'
        p1_name = '---'
        p2_name = '---'
        if p1:
            r = c.execute(text("""
                SELECT pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
                FROM torneos_parejas tp
                JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
                JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
                WHERE tp.id = :pid
            """), {"pid": p1}).fetchone()
            p1_name = r[0][:30] if r else '?'
        if p2:
            r = c.execute(text("""
                SELECT pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
                FROM torneos_parejas tp
                JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
                JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
                WHERE tp.id = :pid
            """), {"pid": p2}).fetchone()
            p2_name = r[0][:30] if r else '?'
        
        print(f"  8vos#{num} [{estado:10}]: {p1_name} [{p1_zona}] vs {p2_name} [{p2_zona}]")
    
    # 4tos
    print("\n=== 4tos ===")
    cuartos = c.execute(text("""
        SELECT p.id_partido, p.numero_partido, p.pareja1_id, p.pareja2_id, p.estado
        FROM partidos p
        WHERE p.id_torneo = 38 AND p.categoria_id = 87 AND p.fase = '4tos'
        ORDER BY p.numero_partido
    """)).fetchall()
    for q in cuartos:
        pid, num, p1, p2, estado = q
        p1_zona = pareja_zona_map.get(p1, '---') if p1 else 'TBD'
        p2_zona = pareja_zona_map.get(p2, '---') if p2 else 'TBD'
        print(f"  4tos#{num}: p1={p1} [{p1_zona}] vs p2={p2} [{p2_zona}] | {estado}")
