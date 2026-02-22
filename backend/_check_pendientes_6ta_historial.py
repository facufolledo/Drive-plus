"""Verificar si los jugadores de los partidos pendientes de 6ta tienen
historial de rating en T38 que sugiera resultados borrados."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))

pendientes = [469, 471, 475, 478, 479, 480, 481, 482]

with e.connect() as c:
    for pid in pendientes:
        p = c.execute(text("""
            SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.zona_id, z.nombre,
                   p.fecha_hora, p.estado,
                   tp1.jugador1_id as p1j1, tp1.jugador2_id as p1j2,
                   tp2.jugador1_id as p2j1, tp2.jugador2_id as p2j2
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            LEFT JOIN torneo_zonas z ON p.zona_id = z.id
            WHERE p.id_partido = :pid
        """), {"pid": pid}).fetchone()
        
        if not p:
            print(f"P{pid}: NO EXISTE")
            continue
        
        # Nombres
        nombres = {}
        for uid in [p[7], p[8], p[9], p[10]]:
            n = c.execute(text("SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = :uid"), {"uid": uid}).fetchone()
            nombres[uid] = f"{n[0]} {n[1]}" if n else f"ID{uid}"
        
        fh = p[5].strftime('%a %d/%m %H:%M') if p[5] else '?'
        print(f"\n{'='*60}")
        print(f"P{pid} | {p[4]} | {fh} | estado={p[6]}")
        print(f"  p1({p[1]}): {nombres[p[7]]} / {nombres[p[8]]}")
        print(f"  p2({p[2]}): {nombres[p[9]]} / {nombres[p[10]]}")
        
        # Buscar historial de rating para estos jugadores en T38
        jugadores = [p[7], p[8], p[9], p[10]]
        for uid in jugadores:
            hist = c.execute(text("""
                SELECT hr.id_partido, hr.rating_antes, hr.rating_despues, hr.delta, hr.creado_en
                FROM historial_rating hr
                JOIN partidos p ON hr.id_partido = p.id_partido
                WHERE hr.id_usuario = :uid AND p.id_torneo = 38
                ORDER BY hr.creado_en
            """), {"uid": uid}).fetchall()
            if hist:
                print(f"  📊 {nombres[uid]} (ID {uid}) - {len(hist)} registros historial T38:")
                for h in hist:
                    partido_ref = c.execute(text("SELECT estado FROM partidos WHERE id_partido = :pid"), {"pid": h[0]}).fetchone()
                    estado_ref = partido_ref[0] if partido_ref else "NO EXISTE"
                    print(f"     partido=P{h[0]}({estado_ref}) {h[1]}→{h[2]} (delta={h[3]}) {h[4]}")
            else:
                print(f"  📊 {nombres[uid]} (ID {uid}) - SIN historial T38")
