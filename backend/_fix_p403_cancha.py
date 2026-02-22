import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Mover P403 a Cancha 7 (ID 78) que está libre a las 16:00
    c.execute(text("UPDATE partidos SET cancha_id = 78 WHERE id_partido = 403"))
    c.commit()
    
    # Verificar todos a las 16:00
    rows = c.execute(text("""
        SELECT p.id_partido, tc.nombre, tcat.nombre as cat,
               p1.nombre || ' ' || p1.apellido as j1p1, p2.nombre || ' ' || p2.apellido as j2p1
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        JOIN torneo_categorias tcat ON p.categoria_id = tcat.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1 ON tp1.jugador1_id = p1.id_usuario
        JOIN perfil_usuarios p2 ON tp1.jugador2_id = p2.id_usuario
        WHERE p.id_torneo = 38 AND p.fecha_hora = '2026-02-21 16:00:00'
        ORDER BY tc.nombre
    """)).fetchall()
    print("Partidos a las 16:00 sáb 21/02:")
    for r in rows:
        print(f"  P{r[0]} | {r[1]} | {r[2]} | {r[3]}/{r[4]}")
