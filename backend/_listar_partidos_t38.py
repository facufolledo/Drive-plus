"""Listar todos los partidos del torneo 38 con nombres de parejas, ordenados por fecha/hora"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from collections import defaultdict
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 38
CATS = {87: "4ta", 88: "6ta", 89: "8va"}
DIAS = {4: "Vie", 5: "Sáb", 6: "Dom"}

with engine.connect() as c:
    # Nombres de parejas
    parejas = {}
    rows = c.execute(text("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.categoria_id,
               p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
        FROM torneos_parejas tp
        JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
        JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
        WHERE tp.torneo_id = :t
    """), {"t": TORNEO_ID}).fetchall()
    for r in rows:
        parejas[r[0]] = {"j1": r[4], "j2": r[5], "cat_id": r[3], "j1_id": r[1], "j2_id": r[2]}

    # Partidos
    partidos = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, p.pareja1_id, p.pareja2_id,
               p.categoria_id, cn.nombre as cancha
        FROM partidos p
        LEFT JOIN torneo_canchas cn ON p.cancha_id = cn.id
        WHERE p.id_torneo = :t AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora, p.cancha_id
    """), {"t": TORNEO_ID}).fetchall()

    def nombre_pareja(pid):
        if pid in parejas:
            p = parejas[pid]
            return f"{p['j1']}/{p['j2']}"
        return f"Pareja {pid}"

    print("=" * 100)
    print(f"TODOS LOS PARTIDOS TORNEO 38 - Ordenados por horario")
    print("=" * 100)

    current_day = None
    for p in partidos:
        pid, fecha, cancha_id, p1, p2, cat_id, cancha = p
        dia = DIAS.get(fecha.weekday(), fecha.strftime("%a"))
        hora = fecha.strftime("%H:%M")
        cat = CATS.get(cat_id, str(cat_id))

        day_key = fecha.strftime("%Y-%m-%d")
        if day_key != current_day:
            current_day = day_key
            print(f"\n{'─' * 100}")
            print(f"  {dia} {fecha.strftime('%d/%m')}")
            print(f"{'─' * 100}")

        print(f"  {hora} | {cancha or 'Sin cancha':10} | {cat:4} | P{pid:3d} | {nombre_pareja(p1):40} vs {nombre_pareja(p2)}")

    # Ahora mostrar conflictos con nombres
    from datetime import timedelta
    DURACION = timedelta(minutes=90)
    MIN_DESCANSO = timedelta(hours=3)

    plist = []
    for p in partidos:
        plist.append({
            "id": p[0], "fecha": p[1], "cancha_id": p[2], "cancha": p[6],
            "p1": p[3], "p2": p[4], "cat_id": p[5], "cat": CATS.get(p[5], "?")
        })

    print(f"\n\n{'=' * 100}")
    print("CONFLICTOS DE CANCHA (misma cancha, < 90 min entre partidos)")
    print("=" * 100)
    for i, a in enumerate(plist):
        for b in plist[i+1:]:
            if a["cancha_id"] == b["cancha_id"] and a["cancha_id"]:
                fin_a = a["fecha"] + DURACION
                if b["fecha"] < fin_a:
                    dia_a = DIAS.get(a["fecha"].weekday(), "?")
                    dia_b = DIAS.get(b["fecha"].weekday(), "?")
                    print(f"\n  ❌ {a['cancha']}:")
                    print(f"     P{a['id']} {a['cat']:4} {dia_a} {a['fecha'].strftime('%H:%M')} - {nombre_pareja(a['p1'])} vs {nombre_pareja(a['p2'])}")
                    print(f"     P{b['id']} {b['cat']:4} {dia_b} {b['fecha'].strftime('%H:%M')} - {nombre_pareja(b['p1'])} vs {nombre_pareja(b['p2'])}")

    print(f"\n\n{'=' * 100}")
    print("DESCANSO < 3H (misma pareja)")
    print("=" * 100)
    pareja_partidos = defaultdict(list)
    for p in plist:
        pareja_partidos[p["p1"]].append(p)
        pareja_partidos[p["p2"]].append(p)
    for pid, pp in sorted(pareja_partidos.items()):
        pp.sort(key=lambda x: x["fecha"])
        for i in range(len(pp)-1):
            a, b = pp[i], pp[i+1]
            diff = b["fecha"] - a["fecha"]
            if diff < MIN_DESCANSO:
                dia_a = DIAS.get(a["fecha"].weekday(), "?")
                print(f"\n  ⚠️  {nombre_pareja(pid)} (pareja {pid}):")
                print(f"     P{a['id']} {a['cat']:4} {dia_a} {a['fecha'].strftime('%H:%M')} -> P{b['id']} {b['cat']:4} {b['fecha'].strftime('%H:%M')} (dif: {diff})")

    # Cross-cat por jugador
    print(f"\n\n{'=' * 100}")
    print("CROSS-CATEGORÍA < 3H (mismo jugador en distintas categorías)")
    print("=" * 100)
    jugador_partidos = defaultdict(list)
    for p in plist:
        if p["p1"] in parejas:
            jugador_partidos[parejas[p["p1"]]["j1_id"]].append(p)
            jugador_partidos[parejas[p["p1"]]["j2_id"]].append(p)
        if p["p2"] in parejas:
            jugador_partidos[parejas[p["p2"]]["j1_id"]].append(p)
            jugador_partidos[parejas[p["p2"]]["j2_id"]].append(p)

    jnames = {}
    for jid in jugador_partidos:
        r = c.execute(text("SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = :id"), {"id": jid}).fetchone()
        jnames[jid] = f"{r[0]} {r[1]}" if r else f"ID:{jid}"

    for jid, jp in sorted(jugador_partidos.items()):
        cats = set(p["cat_id"] for p in jp)
        if len(cats) <= 1:
            continue
        jp.sort(key=lambda x: x["fecha"])
        for i in range(len(jp)-1):
            a, b = jp[i], jp[i+1]
            if a["cat_id"] != b["cat_id"]:
                diff = b["fecha"] - a["fecha"]
                if diff < MIN_DESCANSO:
                    dia_a = DIAS.get(a["fecha"].weekday(), "?")
                    print(f"\n  ⚠️  {jnames[jid]}:")
                    print(f"     P{a['id']} {a['cat']:4} {dia_a} {a['fecha'].strftime('%H:%M')} -> P{b['id']} {b['cat']:4} {b['fecha'].strftime('%H:%M')} (dif: {diff})")
