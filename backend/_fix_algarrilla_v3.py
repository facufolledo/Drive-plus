"""Corregir P647: tercer set ganador Millicay (656), no Salomón (660)
Y actualizar el pase a semis"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # 1. Ver estado actual del partido y el siguiente
    print("=== ANTES ===")
    p647 = conn.execute(text("""
        SELECT id_partido, fase, estado, pareja1_id, pareja2_id, resultado_padel,
               numero_partido, ganador_pareja_id
        FROM partidos WHERE id_partido = 647
    """)).fetchone()
    print(f"P647: pa1={p647[3]}(Martinez/Salomón) pa2={p647[4]}(Algarrilla/Millicay) ganador={p647[7]} num={p647[6]}")
    print(f"  resultado: {p647[5]}")
    
    # Buscar el partido de semis donde avanzó el ganador de P647
    # numero_partido=2 en cuartos -> siguiente = (2+1)//2 = 1 en semis, slot par (p2)
    semis = conn.execute(text("""
        SELECT id_partido, fase, estado, pareja1_id, pareja2_id, numero_partido, ganador_pareja_id
        FROM partidos
        WHERE id_torneo = 38 AND fase = 'semis'
        ORDER BY numero_partido
    """)).fetchall()
    print(f"\nSemis:")
    for s in semis:
        print(f"  P{s[0]}: num={s[5]} pa1={s[3]} pa2={s[4]} estado={s[2]} ganador={s[6]}")
    
    # El partido de cuartos num=2 alimenta semis num=1, slot p2 (par)
    # Buscar cuál semi tiene a 660 (el ganador incorrecto)
    semi_target = None
    for s in semis:
        if s[3] == 660 or s[4] == 660:
            semi_target = s
            break
    
    if semi_target:
        print(f"\nSemi afectada: P{semi_target[0]} (num={semi_target[5]})")
        print(f"  pa1={semi_target[3]} pa2={semi_target[4]} estado={semi_target[2]}")
    
    # 2. Corregir resultado del P647: tercer set 2-6 ganador equipoB
    nuevo_resultado = {
        'sets': [
            {'gamesEquipoA': 6, 'gamesEquipoB': 2, 'ganador': 'equipoA', 'completado': True},
            {'gamesEquipoA': 0, 'gamesEquipoB': 6, 'ganador': 'equipoB', 'completado': True},
            {'gamesEquipoA': 2, 'gamesEquipoB': 6, 'ganador': 'equipoB', 'completado': True}
        ]
    }
    
    conn.execute(text("""
        UPDATE partidos 
        SET resultado_padel = CAST(:resultado AS jsonb),
            ganador_pareja_id = 656
        WHERE id_partido = 647
    """), {"resultado": json.dumps(nuevo_resultado)})
    print(f"\n✅ P647: resultado corregido, ganador cambiado a 656 (Algarrilla/Millicay)")
    
    # 3. Actualizar la semi: cambiar 660 por 656
    if semi_target:
        semi_id = semi_target[0]
        if semi_target[3] == 660:
            conn.execute(text("UPDATE partidos SET pareja1_id = 656 WHERE id_partido = :sid"), {"sid": semi_id})
            print(f"✅ P{semi_id} (semi): pareja1 cambiada de 660 -> 656")
        elif semi_target[4] == 660:
            conn.execute(text("UPDATE partidos SET pareja2_id = 656 WHERE id_partido = :sid"), {"sid": semi_id})
            print(f"✅ P{semi_id} (semi): pareja2 cambiada de 660 -> 656")
        
        # Si la semi ya tiene resultado, hay que verificar
        if semi_target[2] == 'confirmado':
            print(f"⚠️ ATENCIÓN: La semi P{semi_id} ya está confirmada, revisar manualmente")
    
    conn.commit()
    
    # 4. Verificar
    print("\n=== DESPUÉS ===")
    p647_new = conn.execute(text("""
        SELECT id_partido, pareja1_id, pareja2_id, ganador_pareja_id, resultado_padel
        FROM partidos WHERE id_partido = 647
    """)).fetchone()
    print(f"P647: pa1={p647_new[1]} pa2={p647_new[2]} ganador={p647_new[3]}")
    print(f"  resultado: {p647_new[4]}")
    
    semis2 = conn.execute(text("""
        SELECT id_partido, fase, pareja1_id, pareja2_id, estado, numero_partido
        FROM partidos WHERE id_torneo = 38 AND fase = 'semis' ORDER BY numero_partido
    """)).fetchall()
    print(f"\nSemis actualizadas:")
    for s in semis2:
        print(f"  P{s[0]}: num={s[5]} pa1={s[2]} pa2={s[3]} estado={s[4]}")
