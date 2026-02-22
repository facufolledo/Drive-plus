"""Restaurar resultados de Zona E 6ta desde captura del usuario."""
import os, json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))

def make_resultado(sets_data):
    sets = []
    for gA, gB in sets_data:
        ganador = "equipoA" if gA > gB else "equipoB"
        sets.append({"gamesEquipoA": gA, "gamesEquipoB": gB, "ganador": ganador, "completado": True})
    return json.dumps({"sets": sets})

# Resultados de la captura Zona E
resultados = [
    # P479: Calderón/Calderón(658) vs Martinez/Ceballos(659) -> 3-6 4-6 ganó 659
    (479, 659, [(3,6),(4,6)]),
    # P481: Martinez/Ceballos(659) vs Soria/Quiroz(648) -> 6-2 6-2 ganó 659
    (481, 659, [(6,2),(6,2)]),
]

with e.connect() as c:
    for pid, ganador, sets_data in resultados:
        resultado_json = make_resultado(sets_data)
        p = c.execute(text("SELECT estado, pareja1_id, pareja2_id FROM partidos WHERE id_partido = :pid"), {"pid": pid}).fetchone()
        if not p:
            print(f"  ❌ P{pid} no existe")
            continue
        if p[0] != 'pendiente':
            print(f"  ⚠️ P{pid} ya tiene estado={p[0]}, saltando")
            continue
        
        c.execute(text("""
            UPDATE partidos SET estado = 'confirmado', ganador_pareja_id = :ganador,
                   resultado_padel = CAST(:resultado AS jsonb), elo_aplicado = true
            WHERE id_partido = :pid
        """), {"ganador": ganador, "resultado": resultado_json, "pid": pid})
        
        sets_str = " ".join([f"{s[0]}-{s[1]}" for s in sets_data])
        ganador_str = "p1" if ganador == p[1] else "p2"
        print(f"  ✅ P{pid}: {sets_str} -> ganó {ganador_str} (pareja {ganador})")
    
    c.commit()
    
    # Verificar zona E completa
    print(f"\n--- Zona E 6ta ---")
    rows = c.execute(text("""
        SELECT p.id_partido, p.estado, p.ganador_pareja_id, p.resultado_padel IS NOT NULL
        FROM partidos p WHERE p.zona_id = 207 ORDER BY p.id_partido
    """)).fetchall()
    for r in rows:
        print(f"  P{r[0]}: estado={r[1]} ganador={r[2]} tiene_resultado={r[3]}")
