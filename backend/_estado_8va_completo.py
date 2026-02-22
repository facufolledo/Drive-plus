import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    print("=== TODOS LOS PARTIDOS DE 8VA (cat 89) EN TORNEO 38 ===")
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, tc.nombre as cancha, p.zona_id, tz.nombre as zona_nombre,
               p1n.nombre || ' ' || p1n.apellido || ' / ' || p2n.nombre || ' ' || p2n.apellido as pareja1,
               p3n.nombre || ' ' || p3n.apellido || ' / ' || p4n.nombre || ' ' || p4n.apellido as pareja2,
               p.pareja1_id, p.pareja2_id, p.estado
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
        JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
        WHERE p.id_torneo = 38 AND p.categoria_id = 89
        ORDER BY p.zona_id, p.fecha_hora
    """)).fetchall()
    
    current_zona = None
    for r in rows:
        if r[4] != current_zona:
            current_zona = r[4]
            print(f"\n  --- {r[4]} (zona_id={r[3]}) ---")
        fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
        dia = fh.strftime('%a %d/%m').replace('Fri','VIE').replace('Sat','SÁB').replace('Sun','DOM')
        print(f"  P{r[0]} | {dia} {fh.strftime('%H:%M')} | {r[2]} | PA{r[7]} {r[5]} vs PA{r[8]} {r[6]} | {r[9]}")

    print(f"\n  TOTAL: {len(rows)} partidos en 8va")
