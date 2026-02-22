"""Restaurar resultados de 6ta que se borraron al regenerar fixture.
Datos tomados del video del usuario."""
import os, json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))

def make_resultado(sets_data):
    """sets_data = [(gA, gB), ...] donde gA=games pareja1, gB=games pareja2"""
    sets = []
    for gA, gB in sets_data:
        ganador = "equipoA" if gA > gB else "equipoB"
        sets.append({"gamesEquipoA": gA, "gamesEquipoB": gB, "ganador": ganador, "completado": True})
    return json.dumps({"sets": sets})

# Resultados del video: (id_partido, ganador_pareja_id, sets[(gA,gB),...])
resultados = [
    # Zona A
    (468, 631, [(5,7),(3,6)]),      # Ortiz/Speziale vs Ruarte/Hrellac -> ganó Ruarte (p2=631)
    (467, 625, [(6,4),(6,4)]),      # Ortiz/Speziale vs Samir/Rodozaldovich -> ganó Ortiz (p1=625)
    # Zona B
    (470, 627, [(6,1),(6,1)]),      # Alegre/Tasiukaz vs Giordano/Tapia -> ganó Alegre (p1=627)
    (472, 629, [(1,6),(1,6)]),      # Giordano/Tapia vs Ligorria/Díaz -> ganó Ligorria (p2=629)
    # Zona C
    (473, 626, [(6,4),(0,6),(5,7)]),  # Algarrilla/Montivero vs Díaz/Brizuela -> ganó Díaz (p2=626)
    (474, 620, [(6,4),(4,6),(7,6)]),  # Algarrilla/Montivero vs Oliva/Cruz -> ganó Algarrilla (p1=620)
    # Zona D
    (476, 623, [(0,6),(2,6)]),      # Millicay/Vera vs Farran/Vega -> ganó Farran (p2=623)
    (477, 624, [(4,6),(3,6)]),      # Millicay/Vera vs Lobos/Santander -> ganó Lobos (p2=624)
]

with e.connect() as c:
    for pid, ganador, sets_data in resultados:
        resultado_json = make_resultado(sets_data)
        
        # Verificar que el partido existe y está pendiente
        p = c.execute(text("SELECT estado, pareja1_id, pareja2_id FROM partidos WHERE id_partido = :pid"), {"pid": pid}).fetchone()
        if not p:
            print(f"  ❌ P{pid} no existe")
            continue
        
        # Actualizar resultado (sin aplicar ELO, eso ya se hizo antes y los ratings ya lo tienen)
        c.execute(text("""
            UPDATE partidos SET estado = 'confirmado', ganador_pareja_id = :ganador,
                   resultado_padel = CAST(:resultado AS jsonb), elo_aplicado = true
            WHERE id_partido = :pid
        """), {"ganador": ganador, "resultado": resultado_json, "pid": pid})
        
        sets_str = " ".join([f"{s[0]}-{s[1]}" for s in sets_data])
        ganador_str = "p1" if ganador == p[1] else "p2"
        print(f"  ✅ P{pid}: {sets_str} -> ganó {ganador_str} (pareja {ganador})")
    
    c.commit()
    
    # Verificar
    print(f"\n--- VERIFICACIÓN ---")
    for pid, _, _ in resultados:
        p = c.execute(text("SELECT estado, ganador_pareja_id, resultado_padel IS NOT NULL FROM partidos WHERE id_partido = :pid"), {"pid": pid}).fetchone()
        print(f"  P{pid}: estado={p[0]} ganador={p[1]} tiene_resultado={p[2]}")
    
    # Partidos pendientes
    pend = c.execute(text("""
        SELECT id_partido FROM partidos WHERE id_torneo = 38 AND categoria_id = 88 AND estado = 'pendiente'
    """)).fetchall()
    print(f"\nPartidos 6ta pendientes: {[p[0] for p in pend]}")
