"""Verificar solapamientos completos del torneo 38"""
import os, sys
from datetime import timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

DURACION = timedelta(minutes=50)
MIN_DESCANSO = timedelta(hours=3)

with engine.connect() as c:
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, tc.nombre as cancha,
               p.pareja1_id, p.pareja2_id, p.categoria_id, tcat.nombre as cat,
               tp1.jugador1_id as p1j1, tp1.jugador2_id as p1j2,
               tp2.jugador1_id as p2j1, tp2.jugador2_id as p2j2
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        JOIN torneo_categorias tcat ON p.categoria_id = tcat.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        WHERE p.id_torneo = 38 AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora
    """)).fetchall()

    partidos = []
    for r in rows:
        fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
        partidos.append({
            "id": r[0], "fh": fh, "cancha_id": r[2], "cancha": r[3],
            "p1": r[4], "p2": r[5], "cat_id": r[6], "cat": r[7],
            "jugadores": {r[8], r[9], r[10], r[11]}
        })

    # 1. Solapamiento de cancha (<50 min)
    print("=== 1. SOLAPAMIENTOS DE CANCHA (<50 min) ===")
    cancha_conflicts = 0
    for i, a in enumerate(partidos):
        for b in partidos[i+1:]:
            if a["cancha_id"] != b["cancha_id"]:
                continue
            a_fin = a["fh"] + DURACION
            b_fin = b["fh"] + DURACION
            if a["fh"] < b_fin and b["fh"] < a_fin:
                diff = abs((b["fh"] - a["fh"]).total_seconds()) / 60
                print(f"  ❌ P{a['id']} ({a['cat']}) {a['fh'].strftime('%a %d %H:%M')} vs P{b['id']} ({b['cat']}) {b['fh'].strftime('%a %d %H:%M')} en {a['cancha']} (diff: {diff:.0f}min)")
                cancha_conflicts += 1
    if cancha_conflicts == 0:
        print("  ✅ Sin solapamientos de cancha")

    # 2. Descanso <3h para misma pareja
    print(f"\n=== 2. DESCANSO <3H MISMA PAREJA ===")
    descanso_conflicts = 0
    pareja_partidos = {}
    for p in partidos:
        for pid in [p["p1"], p["p2"]]:
            pareja_partidos.setdefault(pid, []).append(p)
    for pid, pts in pareja_partidos.items():
        pts_sorted = sorted(pts, key=lambda x: x["fh"])
        for i in range(len(pts_sorted) - 1):
            a = pts_sorted[i]
            b = pts_sorted[i+1]
            diff = b["fh"] - a["fh"]
            if diff < MIN_DESCANSO:
                hrs = diff.total_seconds() / 3600
                print(f"  ❌ Pareja {pid}: P{a['id']} ({a['cat']}) {a['fh'].strftime('%a %d %H:%M')} -> P{b['id']} ({b['cat']}) {b['fh'].strftime('%a %d %H:%M')} ({hrs:.1f}h)")
                descanso_conflicts += 1
    if descanso_conflicts == 0:
        print("  ✅ Sin problemas de descanso")

    # 3. Cross-categoría (mismo jugador en 2 partidos <3h)
    print(f"\n=== 3. CROSS-CATEGORÍA (jugador en 2 cats <3h) ===")
    jugador_partidos = {}
    for p in partidos:
        for jid in p["jugadores"]:
            jugador_partidos.setdefault(jid, []).append(p)
    cross_conflicts = 0
    for jid, pts in jugador_partidos.items():
        if len(pts) < 2:
            continue
        cats = set(p["cat_id"] for p in pts)
        if len(cats) < 2:
            continue
        pts_sorted = sorted(pts, key=lambda x: x["fh"])
        for i in range(len(pts_sorted) - 1):
            a = pts_sorted[i]
            b = pts_sorted[i+1]
            if a["cat_id"] == b["cat_id"]:
                continue
            diff = b["fh"] - a["fh"]
            if diff < MIN_DESCANSO:
                hrs = diff.total_seconds() / 3600
                # Get name
                name = c.execute(text("SELECT nombre || ' ' || apellido FROM perfil_usuarios WHERE id_usuario = :j"), {"j": jid}).fetchone()[0]
                print(f"  ❌ {name} (ID {jid}): P{a['id']} ({a['cat']}) {a['fh'].strftime('%a %d %H:%M')} -> P{b['id']} ({b['cat']}) {b['fh'].strftime('%a %d %H:%M')} ({hrs:.1f}h)")
                cross_conflicts += 1
    if cross_conflicts == 0:
        print("  ✅ Sin conflictos cross-categoría")

    print(f"\n=== RESUMEN ===")
    print(f"  Cancha: {cancha_conflicts} | Descanso: {descanso_conflicts} | Cross-cat: {cross_conflicts}")
