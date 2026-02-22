import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, tc.nombre as cancha, z.nombre as zona,
               p1n.nombre || ' ' || p1n.apellido, p2n.nombre || ' ' || p2n.apellido,
               p1n2.nombre || ' ' || p1n2.apellido, p2n2.nombre || ' ' || p2n2.apellido,
               p.pareja1_id, p.pareja2_id, p.estado, p.zona_id
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p1n2 ON tp1.jugador2_id = p1n2.id_usuario
        JOIN perfil_usuarios p2n ON tp2.jugador1_id = p2n.id_usuario
        JOIN perfil_usuarios p2n2 ON tp2.jugador2_id = p2n2.id_usuario
        WHERE p.id_torneo = 38 AND p.categoria_id = 88
        ORDER BY z.nombre, p.fecha_hora
    """)).fetchall()
    
    current_zona = None
    for r in rows:
        if r[3] != current_zona:
            current_zona = r[3]
            print(f"\n{'='*60}")
            print(f"  {current_zona} (zona_id={r[11]})")
            print(f"{'='*60}")
        fh = r[1].strftime('%a %d/%m %H:%M') if r[1] else '?'
        print(f"  P{r[0]} | {fh} | {r[2]} | {r[10]}")
        print(f"    p1({r[8]}): {r[4]} / {r[6]}")
        print(f"    p2({r[9]}): {r[5]} / {r[7]}")
