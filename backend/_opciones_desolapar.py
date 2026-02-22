"""Ver opciones para desolapar P370/P439 y P392/P396"""
import os, sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

DURACION = timedelta(minutes=50)

with engine.connect() as c:
    # Cargar todos los partidos del viernes
    all_pts = c.execute(text("""
        SELECT id_partido, fecha_hora, cancha_id FROM partidos
        WHERE id_torneo = 38 AND fecha_hora IS NOT NULL AND fecha_hora::date = '2026-02-20'
    """)).fetchall()
    
    def is_free(cancha_id, hora, exclude_pid=None):
        """Chequea si cancha está libre a esa hora (50 min)"""
        fin = hora + DURACION
        for p in all_pts:
            if p[0] == exclude_pid or p[2] != cancha_id:
                continue
            fh = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
            pfin = fh + DURACION
            if hora < pfin and fh < fin:
                return False, f"P{p[0]} {fh.strftime('%H:%M')}"
        return True, None

    canchas = [(76,"C5"), (77,"C6"), (78,"C7")]

    # === CONFLICTO 1: P370 (20:50 C5) vs P439 (21:00 C5) ===
    print("=" * 60)
    print("CONFLICTO 1: P370 (6ta 20:50 C5) vs P439 (6ta 21:00 C5)")
    print("=" * 60)
    
    # Opción A: Mover P439 a otra cancha a las 21:00
    print("\nOpción A: Mover P439 a otra cancha (21:00)")
    for cid, cn in canchas:
        if cid == 76: continue
        libre, conf = is_free(cid, datetime(2026,2,20,21,0), 439)
        print(f"  {cn} 21:00: {'✅ LIBRE' if libre else f'❌ {conf}'}")

    # Opción B: Mover P370 a otra cancha a las 20:50
    print("\nOpción B: Mover P370 a otra cancha (20:50)")
    for cid, cn in canchas:
        if cid == 76: continue
        libre, conf = is_free(cid, datetime(2026,2,20,20,50), 370)
        print(f"  {cn} 20:50: {'✅ LIBRE' if libre else f'❌ {conf}'}")

    # Opción C: Mover P439 a 21:50 en C5 (después de P370)
    print("\nOpción C: Mover P439 a 21:50 C5 (después de P370)")
    libre, conf = is_free(76, datetime(2026,2,20,21,50), 439)
    print(f"  C5 21:50: {'✅ LIBRE' if libre else f'❌ {conf}'}")

    # === CONFLICTO 2: P392 (22:00 C6) vs P396 (22:30 C6) ===
    print("\n" + "=" * 60)
    print("CONFLICTO 2: P392 (4ta 22:00 C6) vs P396 (4ta 22:30 C6)")
    print("=" * 60)

    # Opción A: Mover P396 a otra cancha a las 22:30
    print("\nOpción A: Mover P396 a otra cancha (22:30)")
    for cid, cn in canchas:
        if cid == 77: continue
        libre, conf = is_free(cid, datetime(2026,2,20,22,30), 396)
        print(f"  {cn} 22:30: {'✅ LIBRE' if libre else f'❌ {conf}'}")

    # Opción B: Mover P392 a otra cancha a las 22:00
    print("\nOpción B: Mover P392 a otra cancha (22:00)")
    for cid, cn in canchas:
        if cid == 77: continue
        libre, conf = is_free(cid, datetime(2026,2,20,22,0), 392)
        print(f"  {cn} 22:00: {'✅ LIBRE' if libre else f'❌ {conf}'}")

    # Opción C: Mover P396 a 22:50 en C6 (después de P392)
    print("\nOpción C: Mover P396 a 22:50 C6 (después de P392)")
    libre, conf = is_free(77, datetime(2026,2,20,22,50), 396)
    print(f"  C6 22:50: {'✅ LIBRE' if libre else f'❌ {conf}'}")
