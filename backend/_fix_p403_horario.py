import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Ver P403 actual
    p = c.execute(text("SELECT fecha_hora, cancha_id, fecha FROM partidos WHERE id_partido = 403")).fetchone()
    print(f"P403 actual: fecha_hora={p[0]} cancha={p[1]} fecha={p[2]}")
    
    # Ver partidos a las 16:00 del sábado 21/02
    a16 = c.execute(text("""
        SELECT p.id_partido, tc.nombre, p.categoria_id
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id_torneo = 38 AND p.fecha_hora = '2026-02-21 16:00:00'
    """)).fetchall()
    print(f"\nPartidos a las 16:00 sáb 21/02:")
    for r in a16:
        print(f"  P{r[0]} | {r[1]} | cat={r[2]}")
    
    canchas_ocupadas = {r[1] for r in a16}
    print(f"Canchas ocupadas: {canchas_ocupadas}")
    todas = {'Cancha 5','Cancha 6','Cancha 7','Cancha 8'}
    print(f"Canchas libres: {todas - canchas_ocupadas}")
    
    # Cambiar P403 a 16:00 sáb 21/02
    c.execute(text("""
        UPDATE partidos SET fecha_hora = '2026-02-21 16:00:00', fecha = '2026-02-21'
        WHERE id_partido = 403
    """))
    c.commit()
    
    # Verificar
    p2 = c.execute(text("SELECT fecha_hora, cancha_id, fecha FROM partidos WHERE id_partido = 403")).fetchone()
    cancha = c.execute(text("SELECT nombre FROM torneo_canchas WHERE id = :id"), {"id": p2[1]}).fetchone()[0]
    print(f"\nP403 actualizado: fecha_hora={p2[0]} cancha={cancha} fecha={p2[2]}")
