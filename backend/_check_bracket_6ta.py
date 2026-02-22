"""Revisar bracket de eliminación directa de 6ta T38."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))

with e.connect() as c:
    # Partidos de eliminación de 6ta
    rows = c.execute(text("""
        SELECT p.id_partido, p.fase, p.pareja1_id, p.pareja2_id,
               p.estado, p.fecha_hora, p.cancha_id, p.zona_id,
               p.ganador_pareja_id, p.origen
        FROM partidos p
        WHERE p.id_torneo = 38 AND p.categoria_id = 88 
              AND p.fase != 'zona'
        ORDER BY 
            CASE p.fase 
                WHEN '8vos' THEN 1 
                WHEN '4tos' THEN 2 
                WHEN 'semis' THEN 3 
                WHEN 'final' THEN 4 
            END, p.id_partido
    """)).fetchall()
    
    if not rows:
        print("No hay partidos de eliminación directa en 6ta T38")
    else:
        for r in rows:
            # Nombres de parejas
            p1_name = "TBD"
            p2_name = "TBD"
            if r[2]:
                p1 = c.execute(text("""
                    SELECT pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
                    FROM torneos_parejas tp
                    JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
                    JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
                    WHERE tp.id = :pid
                """), {"pid": r[2]}).fetchone()
                if p1: p1_name = p1[0]
            if r[3]:
                p2 = c.execute(text("""
                    SELECT pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
                    FROM torneos_parejas tp
                    JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
                    JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
                    WHERE tp.id = :pid
                """), {"pid": r[3]}).fetchone()
                if p2: p2_name = p2[0]
            
            fh = r[5].strftime('%a %d/%m %H:%M') if r[5] else '?'
            print(f"P{r[0]} | {r[1]} | {r[4]} | {fh} | origen={r[9]}")
            print(f"  p1({r[2]}): {p1_name}")
            print(f"  p2({r[3]}): {p2_name}")
            print()
    
    # También ver las zonas y posiciones
    print("\n=== POSICIONES POR ZONA ===")
    zonas_6ta = c.execute(text("""
        SELECT id, nombre, orden FROM torneo_zonas 
        WHERE torneo_id = 38 AND categoria_id = 88
        ORDER BY orden
    """)).fetchall()
    
    for z in zonas_6ta:
        print(f"\n{z[1]} (id={z[0]}):")
        # Parejas en esta zona con sus resultados
        parejas = c.execute(text("""
            SELECT DISTINCT tp.id, 
                   pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
            FROM partidos p
            JOIN torneos_parejas tp ON tp.id IN (p.pareja1_id, p.pareja2_id)
            JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
            JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
            WHERE p.zona_id = :zid AND p.fase = 'zona'
        """), {"zid": z[0]}).fetchall()
        
        for par in parejas:
            # Contar ganados/perdidos
            ganados = c.execute(text("""
                SELECT COUNT(*) FROM partidos 
                WHERE zona_id = :zid AND fase = 'zona' AND estado = 'confirmado'
                AND ganador_pareja_id = :pid
            """), {"zid": z[0], "pid": par[0]}).scalar()
            perdidos = c.execute(text("""
                SELECT COUNT(*) FROM partidos 
                WHERE zona_id = :zid AND fase = 'zona' AND estado = 'confirmado'
                AND ganador_pareja_id != :pid
                AND (pareja1_id = :pid OR pareja2_id = :pid)
            """), {"zid": z[0], "pid": par[0]}).scalar()
            pendientes = c.execute(text("""
                SELECT COUNT(*) FROM partidos 
                WHERE zona_id = :zid AND fase = 'zona' AND estado = 'pendiente'
                AND (pareja1_id = :pid OR pareja2_id = :pid)
            """), {"zid": z[0], "pid": par[0]}).scalar()
            print(f"  Pareja {par[0]}: {par[1]} -> G:{ganados} P:{perdidos} Pend:{pendientes}")
