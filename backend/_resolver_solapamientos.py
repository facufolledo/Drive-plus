"""Revisar conflictos <50min y ver si se pueden mover a otra cancha"""
import os, sys
from datetime import timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from collections import defaultdict
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 38
CANCHAS = {76: "Cancha 5", 77: "Cancha 6", 78: "Cancha 7"}
CATS = {87: "4ta", 88: "6ta", 89: "8va"}
DURACION = timedelta(minutes=90)

with engine.connect() as c:
    # Nombres parejas
    parejas = {}
    rows = c.execute(text("""
        SELECT tp.id, p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
        FROM torneos_parejas tp
        JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
        JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
        WHERE tp.torneo_id = :t
    """), {"t": TORNEO_ID}).fetchall()
    for r in rows:
        parejas[r[0]] = f"{r[1]}/{r[2]}"

    # Todos los partidos
    partidos = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, p.pareja1_id, p.pareja2_id, p.categoria_id
        FROM partidos p
        WHERE p.id_torneo = :t AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora
    """), {"t": TORNEO_ID}).fetchall()

    plist = [{"id": p[0], "fecha": p[1], "cancha": p[2], "p1": p[3], "p2": p[4], "cat": p[5]} for p in partidos]

    # Agrupar por cancha
    by_cancha = defaultdict(list)
    for p in plist:
        by_cancha[p["cancha"]].append(p)

    # Encontrar conflictos <50 min en misma cancha
    conflictos = []
    for i, a in enumerate(plist):
        for b in plist[i+1:]:
            if a["cancha"] == b["cancha"] and a["cancha"]:
                diff = (b["fecha"] - a["fecha"]).total_seconds() / 60
                if diff < 50:
                    conflictos.append((a, b, diff))

    print(f"Conflictos con <50 min en misma cancha: {len(conflictos)}\n")

    for a, b, diff in conflictos:
        cat_a = CATS.get(a["cat"], "?")
        cat_b = CATS.get(b["cat"], "?")
        cancha_actual = CANCHAS.get(a["cancha"], "?")
        print(f"{'='*80}")
        print(f"CONFLICTO en {cancha_actual} (dif: {int(diff)} min):")
        print(f"  P{a['id']} {cat_a} {a['fecha'].strftime('%a %H:%M')} - {parejas.get(a['p1'],'?')} vs {parejas.get(a['p2'],'?')}")
        print(f"  P{b['id']} {cat_b} {b['fecha'].strftime('%a %H:%M')} - {parejas.get(b['p1'],'?')} vs {parejas.get(b['p2'],'?')}")

        # Para cada partido del conflicto, ver si cabe en otra cancha
        for partido in [a, b]:
            pid = partido["id"]
            fecha = partido["fecha"]
            fin = fecha + DURACION
            cat = CATS.get(partido["cat"], "?")
            otras_canchas = [cid for cid in CANCHAS if cid != partido["cancha"]]

            for oc in otras_canchas:
                # Revisar si hay conflicto en esa cancha
                libre = True
                for op in by_cancha[oc]:
                    op_fin = op["fecha"] + DURACION
                    if fecha < op_fin and op["fecha"] < fin:
                        libre = False
                        break
                if libre:
                    print(f"  ✅ P{pid} ({cat}) se puede mover a {CANCHAS[oc]}")
                else:
                    print(f"  ❌ P{pid} ({cat}) NO cabe en {CANCHAS[oc]}")
        print()
