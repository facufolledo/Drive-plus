import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Buscar P451 y otros partidos de 6ta que tenían resultado
    for pid in [450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464]:
        p = c.execute(text("""
            SELECT id_partido, id_torneo, categoria_id, estado, ganador_pareja_id, resultado_padel, elo_aplicado
            FROM partidos WHERE id_partido = :pid
        """), {"pid": pid}).fetchone()
        if p:
            print(f"P{p[0]}: torneo={p[1]} cat={p[2]} estado={p[3]} ganador={p[4]} resultado={'SÍ' if p[5] else 'NO'} elo={p[6]}")
    
    # Contar todos los partidos de 6ta en T38
    total = c.execute(text("SELECT COUNT(*) FROM partidos WHERE id_torneo = 38 AND categoria_id = 88")).fetchone()[0]
    con_resultado = c.execute(text("SELECT COUNT(*) FROM partidos WHERE id_torneo = 38 AND categoria_id = 88 AND resultado_padel IS NOT NULL")).fetchone()[0]
    print(f"\nTotal 6ta T38: {total}, con resultado: {con_resultado}")
    
    # Buscar partidos de 6ta con resultado en cualquier estado
    with_res = c.execute(text("""
        SELECT id_partido, estado, ganador_pareja_id, resultado_padel, zona_id
        FROM partidos WHERE id_torneo = 38 AND categoria_id = 88 AND (resultado_padel IS NOT NULL OR ganador_pareja_id IS NOT NULL)
    """)).fetchall()
    print(f"Partidos 6ta con resultado/ganador: {len(with_res)}")
    for r in with_res:
        print(f"  P{r[0]}: estado={r[1]} ganador={r[2]} zona={r[4]}")
    
    # Verificar P451 específicamente
    p451 = c.execute(text("SELECT * FROM partidos WHERE id_partido = 451")).fetchone()
    if p451:
        cols = c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='partidos' ORDER BY ordinal_position")).fetchall()
        col_names = [c[0] for c in cols]
        print(f"\nP451 completo:")
        for i, col in enumerate(col_names):
            if i < len(p451):
                print(f"  {col}: {p451[i]}")
