"""
Script para corregir las semifinales cuando las parejas quedaron en el cuadro equivocado.
Usa la misma lógica que el front: intercambiar-parejas (slot 1 del partido 1 con slot 2 del partido 2)
para dejar Barrera vs Millicay en la semifinal de arriba.

Uso:
  python corregir_semifinales_script.py              # torneo 37, categoría 2
  python corregir_semifinales_script.py 40 1
  python corregir_semifinales_script.py 40 1 -y
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# Misma lógica que el backend: Session + modelo Partido
from src.database.config import SessionLocal
from src.models.driveplus_models import Partido

# Slots como en el endpoint intercambiar-parejas: 1 = pareja1, 2 = pareja2
SLOT_SEMIS_1 = 1   # intercambiar pareja1 de semifinal 1 (TBD)
SLOT_SEMIS_2 = 2   # con pareja2 de semifinal 2 (Barrera)


def corregir_semifinales(torneo_id: int, categoria_id: int, confirmar: bool = True) -> bool:
    db = SessionLocal()
    try:
        # Mismo filtro que el controller: fase in playoffs
        query = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final']),
        )
        if categoria_id is None:
            query = query.filter(Partido.categoria_id.is_(None))
        else:
            query = query.filter(Partido.categoria_id == categoria_id)

        # Diagnóstico: partidos por fase
        from sqlalchemy import func
        diag = db.query(Partido.fase, func.count(Partido.id_partido)).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final']),
        )
        if categoria_id is None:
            diag = diag.filter(Partido.categoria_id.is_(None))
        else:
            diag = diag.filter(Partido.categoria_id == categoria_id)
        diag = diag.group_by(Partido.fase).all()
        if not diag:
            # Mostrar en qué categorías sí hay playoffs para este torneo
            por_cat = db.query(Partido.categoria_id, Partido.fase, func.count(Partido.id_partido)).filter(
                Partido.id_torneo == torneo_id,
                Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final']),
            ).group_by(Partido.categoria_id, Partido.fase).all()
            if por_cat:
                from collections import defaultdict
                by_cat = defaultdict(dict)
                for c, f, n in por_cat:
                    by_cat[c or "NULL"][f] = n
                cats = sorted(k for k in by_cat if k != "NULL" and isinstance(k, int))
                print(f"\n❌ No hay partidos de playoff para torneo {torneo_id}, categoría {categoria_id}.")
                print(f"   Para este torneo hay playoffs en categorías: {cats}")
                print(f"   Por categoría: {dict(by_cat)}")
                if cats:
                    print(f"   Ejemplo: python corregir_semifinales_script.py {torneo_id} {cats[0]} -y")
            else:
                print(f"\n❌ No hay partidos de playoff para torneo {torneo_id} en ninguna categoría.")
            return False
        print(f"\nPartidos por fase: {dict(diag)}")

        # Solo semifinales, orden por numero_partido (igual que listar)
        query = query.filter(Partido.fase.in_(['semis', 'semifinal'])).order_by(Partido.numero_partido)
        partidos = query.all()

        if len(partidos) != 2:
            print(f"\n❌ Se esperaban 2 partidos de semifinales, hay {len(partidos)}.")
            return False

        pa, pb = partidos[0], partidos[1]
        # Misma lógica que intercambiar_parejas_playoff: slot_a=1 (pareja1 semis 1), slot_b=2 (pareja2 semis 2)
        id_a = pa.pareja1_id if SLOT_SEMIS_1 == 1 else pa.pareja2_id
        id_b = pb.pareja1_id if SLOT_SEMIS_2 == 1 else pb.pareja2_id

        print(f"\n=== SEMIFINALES (torneo {torneo_id}, categoría {categoria_id}) ===")
        print(f"  Semifinal 1 (arriba): pareja1={pa.pareja1_id} vs pareja2={pa.pareja2_id} (id_partido={pa.id_partido})")
        print(f"  Semifinal 2 (abajo):  pareja1={pb.pareja1_id} vs pareja2={pb.pareja2_id} (id_partido={pb.id_partido})")
        print(f"\n=== CORRECCIÓN (misma lógica que Intercambiar parejas en el front) ===")
        print(f"  Se intercambia slot {SLOT_SEMIS_1} del partido 1 con slot {SLOT_SEMIS_2} del partido 2.")
        print(f"  Queda: Semifinal 1 = ({id_b}, {pa.pareja2_id})  →  Barrera vs Millicay")
        print(f"         Semifinal 2 = ({pb.pareja1_id}, {id_a})  →  TBD vs TBD")

        if confirmar:
            r = input("\n¿Confirmar? (s/n): ").strip().lower()
            if r != "s":
                print("Cancelado.")
                return False

        # Mismo swap que el controller
        if SLOT_SEMIS_1 == 1:
            pa.pareja1_id = id_b
        else:
            pa.pareja2_id = id_b
        if SLOT_SEMIS_2 == 1:
            pb.pareja1_id = id_a
        else:
            pb.pareja2_id = id_a
        db.commit()

        print("\n✅ Semifinales corregidas. Recargá el bracket en la app.")
        return True
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    ap = argparse.ArgumentParser(description="Corregir parejas en semifinales (Barrera vs Millicay en el mismo cuadro)")
    ap.add_argument("torneo_id", nargs="?", type=int, default=37, help="ID del torneo")
    ap.add_argument("categoria_id", nargs="?", type=int, default=2, help="ID de la categoría")
    ap.add_argument("-y", "--yes", action="store_true", help="No pedir confirmación")
    args = ap.parse_args()

    print(f"Conectando a DB... (torneo={args.torneo_id}, categoría={args.categoria_id})")
    ok = corregir_semifinales(args.torneo_id, args.categoria_id, confirmar=not args.yes)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
