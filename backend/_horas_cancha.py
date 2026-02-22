"""Calcular horas de cancha por día y por cancha"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from collections import defaultdict
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 38
CANCHAS = {76: "Cancha 5", 77: "Cancha 6", 78: "Cancha 7"}
DIAS = {"2026-02-20": "Viernes", "2026-02-21": "Sábado", "2026-02-22": "Domingo"}
DURACION_MIN = 90

with engine.connect() as c:
    rows = c.execute(text("""
        SELECT id_partido, fecha_hora, cancha_id FROM partidos
        WHERE id_torneo = :t AND fecha_hora IS NOT NULL
        ORDER BY fecha_hora
    """), {"t": TORNEO_ID}).fetchall()

    # Por día y cancha
    uso = defaultdict(lambda: defaultdict(list))
    for r in rows:
        f = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
        dia = f.strftime("%Y-%m-%d")
        uso[dia][r[2]].append(f)

    total_horas_dia = defaultdict(float)

    for dia in sorted(uso.keys()):
        nombre_dia = DIAS.get(dia, dia)
        print(f"\n{'='*60}")
        print(f"  {nombre_dia} ({dia})")
        print(f"{'='*60}")
        dia_total = 0
        for cid in sorted(CANCHAS.keys()):
            partidos = sorted(uso[dia].get(cid, []))
            if not partidos:
                continue
            horas = len(partidos) * DURACION_MIN / 60
            primer = partidos[0].strftime("%H:%M")
            ultimo_fin = (partidos[-1].__class__(partidos[-1].year, partidos[-1].month, partidos[-1].day,
                          partidos[-1].hour, partidos[-1].minute) 
                          if True else None)
            from datetime import timedelta
            ultimo_fin = partidos[-1] + timedelta(minutes=DURACION_MIN)
            rango = f"{primer} - {ultimo_fin.strftime('%H:%M')}"
            print(f"  {CANCHAS[cid]}: {len(partidos)} partidos = {horas:.1f}h de juego | Rango: {rango}")
            dia_total += horas
        
        total_horas_dia[dia] = dia_total
        print(f"  --- Total día: {dia_total:.1f}h de cancha")

    print(f"\n{'='*60}")
    print("RESUMEN PARA PEDIR CANCHAS")
    print(f"{'='*60}")
    for dia in sorted(uso.keys()):
        nombre_dia = DIAS.get(dia, dia)
        # Calcular rango real (primer partido a último partido + 90min)
        todos = []
        for cid in uso[dia]:
            todos.extend(uso[dia][cid])
        todos.sort()
        if todos:
            from datetime import timedelta
            inicio = todos[0]
            fin = todos[-1] + timedelta(minutes=DURACION_MIN)
            canchas_usadas = len([cid for cid in CANCHAS if uso[dia].get(cid)])
            print(f"  {nombre_dia}: {canchas_usadas} canchas, {inicio.strftime('%H:%M')} a {fin.strftime('%H:%M')} ({total_horas_dia[dia]:.1f}h de juego total)")
