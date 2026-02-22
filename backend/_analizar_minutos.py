"""Analizar si moviendo pocos minutos se resuelven los 2 conflictos restantes"""
import os, sys
from datetime import timedelta, datetime
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from collections import defaultdict
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 38
CANCHAS = {76: "Cancha 5", 77: "Cancha 6", 78: "Cancha 7"}
DURACION = timedelta(minutes=90)

with engine.connect() as c:
    partidos = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id
        FROM partidos p WHERE p.id_torneo = :t AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora
    """), {"t": TORNEO_ID}).fetchall()

    by_cancha = defaultdict(list)
    for p in partidos:
        f = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
        by_cancha[p[2]].append({"id": p[0], "fecha": f})

    def check_fit(cancha_id, fecha_propuesta):
        """Retorna True si un partido de 90min a fecha_propuesta cabe en la cancha"""
        fin = fecha_propuesta + DURACION
        for op in by_cancha[cancha_id]:
            op_fin = op["fecha"] + DURACION
            if fecha_propuesta < op_fin and op["fecha"] < fin:
                return False, op
        return True, None

    # CONFLICTO 1: P392 y P396 ambos Cancha 6, Vie 22:00
    print("=" * 80)
    print("CONFLICTO: P392 y P396 en Cancha 6, Vie 22:00")
    print("=" * 80)
    # Intentar mover P396 unos minutos antes o después, en cualquier cancha
    for pid_mover in [396, 392]:
        print(f"\n  Intentando mover P{pid_mover}:")
        base = datetime(2026, 2, 20, 22, 0)  # vie 22:00
        for delta in [-20, -10, 10, 20, 30, -30]:
            nueva = base + timedelta(minutes=delta)
            for cid in CANCHAS:
                fits, conflict = check_fit(cid, nueva)
                # Excluir el propio partido del check
                if not fits and conflict and conflict["id"] == pid_mover:
                    fits = True
                if fits:
                    print(f"    ✅ P{pid_mover} -> {CANCHAS[cid]} {nueva.strftime('%H:%M')} (delta: {delta:+d} min)")
                    break
            else:
                print(f"    ❌ {nueva.strftime('%H:%M')} ({delta:+d} min) - no cabe en ninguna cancha")

    # CONFLICTO 2: P433 (Cancha 5, Sáb 14:50) y P395 (Cancha 5, Sáb 15:00)
    print(f"\n{'=' * 80}")
    print("CONFLICTO: P433 y P395 en Cancha 5, Sáb 14:50/15:00")
    print("=" * 80)
    for pid_mover, base_hora in [(433, datetime(2026, 2, 21, 14, 50)), (395, datetime(2026, 2, 21, 15, 0))]:
        print(f"\n  Intentando mover P{pid_mover} (actual {base_hora.strftime('%H:%M')}):")
        for delta in [-20, -10, 10, 20, 30, -30, -40, 40]:
            nueva = base_hora + timedelta(minutes=delta)
            for cid in CANCHAS:
                # Check fit excluyendo el propio partido
                fin = nueva + DURACION
                ok = True
                for op in by_cancha[cid]:
                    if op["id"] == pid_mover:
                        continue
                    op_fin = op["fecha"] + DURACION
                    if nueva < op_fin and op["fecha"] < fin:
                        ok = False
                        break
                if ok:
                    print(f"    ✅ P{pid_mover} -> {CANCHAS[cid]} {nueva.strftime('%H:%M')} (delta: {delta:+d} min)")
                    break
            else:
                print(f"    ❌ {nueva.strftime('%H:%M')} ({delta:+d} min) - no cabe en ninguna cancha")
