"""Restaurar P480: Calderón/Calderón vs Soria/Quiroz 6-4 7-5"""
import os, json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))

sets_data = [(6,4),(7,5)]
sets = []
for gA, gB in sets_data:
    ganador = "equipoA" if gA > gB else "equipoB"
    sets.append({"gamesEquipoA": gA, "gamesEquipoB": gB, "ganador": ganador, "completado": True})
resultado_json = json.dumps({"sets": sets})

with e.connect() as c:
    p = c.execute(text("SELECT estado, pareja1_id, pareja2_id FROM partidos WHERE id_partido = 480"), {}).fetchone()
    print(f"P480: estado={p[0]} p1={p[1]} p2={p[2]}")
    
    # Ganó Calderón/Calderón = p1 = 658
    c.execute(text("""
        UPDATE partidos SET estado = 'confirmado', ganador_pareja_id = 658,
               resultado_padel = CAST(:resultado AS jsonb), elo_aplicado = true
        WHERE id_partido = 480
    """), {"resultado": resultado_json})
    c.commit()
    
    p = c.execute(text("SELECT estado, ganador_pareja_id, resultado_padel IS NOT NULL FROM partidos WHERE id_partido = 480"), {}).fetchone()
    print(f"✅ P480: estado={p[0]} ganador={p[1]} tiene_resultado={p[2]}")
    
    # Estado final Zona E
    print(f"\n--- Zona E completa ---")
    rows = c.execute(text("""
        SELECT p.id_partido, p.estado, p.ganador_pareja_id
        FROM partidos p WHERE p.zona_id = 207 ORDER BY p.id_partido
    """)).fetchall()
    for r in rows:
        print(f"  P{r[0]}: estado={r[1]} ganador={r[2]}")
