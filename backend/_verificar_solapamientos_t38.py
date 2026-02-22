"""Verificar solapamientos torneo 38 - todas las categorías (4ta=87, 6ta=88, 8va=89)"""
import os, sys
from datetime import timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 38
CATS = {87: "4ta", 88: "6ta", 89: "8va"}
DURACION_PARTIDO = timedelta(minutes=90)
MIN_DESCANSO = timedelta(hours=3)

with engine.connect() as c:
    # Traer todos los partidos programados del torneo 38
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, p.pareja1_id, p.pareja2_id,
               tc.nombre as cat_nombre, p.categoria_id,
               cn.nombre as cancha_nombre
        FROM partidos p
        LEFT JOIN torneo_categorias tc ON p.categoria_id = tc.id
        LEFT JOIN torneo_canchas cn ON p.cancha_id = cn.id
        WHERE p.id_torneo = :t AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora
    """), {"t": TORNEO_ID}).fetchall()

    print(f"Total partidos programados: {len(rows)}")
    print()

    # Mapear pareja -> jugadores para detectar solapamientos cross-categoria por jugador
    parejas_jugadores = {}
    prows = c.execute(text("""
        SELECT id, jugador1_id, jugador2_id, categoria_id
        FROM torneos_parejas WHERE torneo_id = :t
    """), {"t": TORNEO_ID}).fetchall()
    for pr in prows:
        parejas_jugadores[pr[0]] = (pr[1], pr[2], pr[3])

    # Estructurar partidos
    partidos = []
    for r in rows:
        partidos.append({
            "id": r[0], "fecha": r[1], "cancha_id": r[2],
            "p1": r[3], "p2": r[4], "cat": r[5] or CATS.get(r[6], "?"),
            "cat_id": r[6], "cancha": r[7] or f"Cancha {r[2]}"
        })

    errores = []

    # 1. Solapamiento de cancha (misma cancha, mismo horario)
    print("=" * 70)
    print("1. SOLAPAMIENTO DE CANCHA")
    print("=" * 70)
    for i, a in enumerate(partidos):
        for b in partidos[i+1:]:
            if a["cancha_id"] == b["cancha_id"] and a["cancha_id"] is not None:
                fin_a = a["fecha"] + DURACION_PARTIDO
                fin_b = b["fecha"] + DURACION_PARTIDO
                if a["fecha"] < fin_b and b["fecha"] < fin_a:
                    msg = (f"CANCHA {a['cancha']}: Partido {a['id']} ({a['cat']}) "
                           f"{a['fecha'].strftime('%a %H:%M')} vs "
                           f"Partido {b['id']} ({b['cat']}) {b['fecha'].strftime('%a %H:%M')}")
                    errores.append(("CANCHA", msg))
                    print(f"  ❌ {msg}")

    if not any(e[0] == "CANCHA" for e in errores):
        print("  ✅ Sin solapamientos de cancha")

    # 2. Solapamiento de pareja (misma pareja juega 2 partidos al mismo tiempo)
    print()
    print("=" * 70)
    print("2. SOLAPAMIENTO DE PAREJA (mismo horario)")
    print("=" * 70)
    for i, a in enumerate(partidos):
        parejas_a = {a["p1"], a["p2"]}
        for b in partidos[i+1:]:
            parejas_b = {b["p1"], b["p2"]}
            comun = parejas_a & parejas_b
            if comun:
                fin_a = a["fecha"] + DURACION_PARTIDO
                fin_b = b["fecha"] + DURACION_PARTIDO
                if a["fecha"] < fin_b and b["fecha"] < fin_a:
                    msg = (f"Pareja(s) {comun}: Partido {a['id']} ({a['cat']}) "
                           f"{a['fecha'].strftime('%a %H:%M')} vs "
                           f"Partido {b['id']} ({b['cat']}) {b['fecha'].strftime('%a %H:%M')}")
                    errores.append(("PAREJA_SOLAP", msg))
                    print(f"  ❌ {msg}")

    if not any(e[0] == "PAREJA_SOLAP" for e in errores):
        print("  ✅ Sin solapamientos de pareja")

    # 3. Mínimo 3 horas entre partidos de la misma pareja (DENTRO de cada categoría)
    print()
    print("=" * 70)
    print("3. DESCANSO MÍNIMO 3H ENTRE PARTIDOS (misma pareja, misma categoría)")
    print("=" * 70)
    from collections import defaultdict
    pareja_partidos = defaultdict(list)
    for p in partidos:
        pareja_partidos[p["p1"]].append(p)
        pareja_partidos[p["p2"]].append(p)

    for pareja_id, plist in sorted(pareja_partidos.items()):
        # Filtrar por categoría
        by_cat = defaultdict(list)
        for p in plist:
            by_cat[p["cat_id"]].append(p)
        for cat_id, cat_partidos in by_cat.items():
            cat_partidos.sort(key=lambda x: x["fecha"])
            for i in range(len(cat_partidos) - 1):
                a = cat_partidos[i]
                b = cat_partidos[i + 1]
                diff = b["fecha"] - a["fecha"]
                if diff < MIN_DESCANSO:
                    cat_name = CATS.get(cat_id, str(cat_id))
                    msg = (f"Pareja {pareja_id} ({cat_name}): "
                           f"Partido {a['id']} {a['fecha'].strftime('%a %H:%M')} -> "
                           f"Partido {b['id']} {b['fecha'].strftime('%a %H:%M')} "
                           f"(diferencia: {diff})")
                    errores.append(("DESCANSO_CAT", msg))
                    print(f"  ⚠️  {msg}")

    if not any(e[0] == "DESCANSO_CAT" for e in errores):
        print("  ✅ Todas las parejas tienen 3h+ entre partidos")

    # 4. Solapamiento cross-categoría por JUGADOR
    print()
    print("=" * 70)
    print("4. SOLAPAMIENTO CROSS-CATEGORÍA (mismo jugador en distintas categorías)")
    print("=" * 70)
    jugador_partidos = defaultdict(list)
    for p in partidos:
        if p["p1"] in parejas_jugadores:
            j1, j2, _ = parejas_jugadores[p["p1"]]
            jugador_partidos[j1].append(p)
            jugador_partidos[j2].append(p)
        if p["p2"] in parejas_jugadores:
            j1, j2, _ = parejas_jugadores[p["p2"]]
            jugador_partidos[j1].append(p)
            jugador_partidos[j2].append(p)

    # Buscar nombres de jugadores para mejor output
    all_jids = set(jugador_partidos.keys())
    jnames = {}
    if all_jids:
        for jid in all_jids:
            r = c.execute(text(
                "SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = :id"
            ), {"id": jid}).fetchone()
            if r:
                jnames[jid] = f"{r[0]} {r[1]}"
            else:
                jnames[jid] = f"ID:{jid}"

    for jid, jplist in sorted(jugador_partidos.items()):
        # Solo revisar si juega en más de 1 categoría
        cats_jugador = set(p["cat_id"] for p in jplist)
        if len(cats_jugador) <= 1:
            continue
        jplist.sort(key=lambda x: x["fecha"])
        for i in range(len(jplist) - 1):
            a = jplist[i]
            b = jplist[i + 1]
            if a["cat_id"] != b["cat_id"]:
                diff = b["fecha"] - a["fecha"]
                if diff < MIN_DESCANSO:
                    msg = (f"Jugador {jnames.get(jid, jid)}: "
                           f"Partido {a['id']} ({a['cat']}) {a['fecha'].strftime('%a %H:%M')} -> "
                           f"Partido {b['id']} ({b['cat']}) {b['fecha'].strftime('%a %H:%M')} "
                           f"(diferencia: {diff})")
                    errores.append(("CROSS_CAT", msg))
                    print(f"  ⚠️  {msg}")

    if not any(e[0] == "CROSS_CAT" for e in errores):
        print("  ✅ Sin solapamientos cross-categoría")

    # Resumen
    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Total partidos: {len(partidos)}")
    for cat_id, cat_name in CATS.items():
        cnt = sum(1 for p in partidos if p["cat_id"] == cat_id)
        print(f"  {cat_name}: {cnt} partidos")
    print(f"Errores encontrados: {len(errores)}")
    for tipo in ["CANCHA", "PAREJA_SOLAP", "DESCANSO_CAT", "CROSS_CAT"]:
        cnt = sum(1 for e in errores if e[0] == tipo)
        if cnt:
            print(f"  {tipo}: {cnt}")
    if not errores:
        print("✅ TODO OK - Sin solapamientos ni problemas de descanso")
