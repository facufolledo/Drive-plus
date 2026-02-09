"""
Script para intercambiar el primer y el último cuadro de cuartos de final.
Objetivo típico: subir el cuadro de abajo (ej. Barrera/Folledo) y bajar el de arriba (ej. Giordano/Leterucci)
para que quede Barrera vs Millicay en semifinales.

Uso:
  python intercambiar_cuartos_script.py                    # torneo 37, categoría 2 (7ma)
  python intercambiar_cuartos_script.py 37 2
  python intercambiar_cuartos_script.py --torneo 40 --categoria 1 -y
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Falta DATABASE_URL en .env")
    sys.exit(1)

if "pg8000" not in DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
    elif DATABASE_URL.startswith("postgresql+psycopg2://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+pg8000://", 1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def intercambiar_cuartos(torneo_id: int, categoria_id: int, confirmar: bool = True) -> bool:
    session = Session()
    try:
        # Diagnóstico: ver cuántos partidos hay por fase para este torneo/categoría
        if categoria_id is None:
            diag = session.execute(text("""
                SELECT p.fase, COUNT(*) AS c
                FROM partidos p
                WHERE p.id_torneo = :torneo_id AND p.categoria_id IS NULL
                GROUP BY p.fase
            """), {"torneo_id": torneo_id}).fetchall()
        else:
            diag = session.execute(text("""
                SELECT p.fase, COUNT(*) AS c
                FROM partidos p
                WHERE p.id_torneo = :torneo_id AND p.categoria_id = :cat_id
                GROUP BY p.fase
            """), {"torneo_id": torneo_id, "cat_id": categoria_id}).fetchall()
        if not diag:
            print(f"\n❌ No hay partidos de playoff para torneo {torneo_id}, categoría {categoria_id}.")
            return False
        print(f"\nPartidos por fase: {dict((r.fase, r.c) for r in diag)}")

        # En la DB la fase puede estar como '4tos' o 'cuartos'
        if categoria_id is None:
            partidos = session.execute(text("""
                SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.numero_partido
                FROM partidos p
                WHERE p.id_torneo = :torneo_id
                  AND p.fase IN ('cuartos', '4tos')
                  AND p.categoria_id IS NULL
                ORDER BY p.numero_partido
            """), {"torneo_id": torneo_id}).fetchall()
        else:
            partidos = session.execute(text("""
                SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.numero_partido
                FROM partidos p
                WHERE p.id_torneo = :torneo_id
                  AND p.fase IN ('cuartos', '4tos')
                  AND p.categoria_id = :cat_id
                ORDER BY p.numero_partido
            """), {"torneo_id": torneo_id, "cat_id": categoria_id}).fetchall()

        print(f"\n=== CUARTOS (torneo {torneo_id}, categoría {categoria_id}) ===")
        for i, p in enumerate(partidos):
            print(f"  {p.numero_partido}. Pareja {p.pareja1_id or '?'} vs {p.pareja2_id or '?'} (id_partido={p.id_partido})")

        if len(partidos) < 2:
            print(f"\n❌ Se necesitan al menos 2 partidos de cuartos, hay {len(partidos)}.")
            return False

        primero = partidos[0]
        ultimo = partidos[-1]

        print(f"\n=== INTERCAMBIO ===")
        print(f"  Arriba (posición 1) ← cuadro que estaba abajo (id={ultimo.id_partido})")
        print(f"  Abajo (posición {ultimo.numero_partido}) ← cuadro que estaba arriba (id={primero.id_partido})")

        if confirmar:
            r = input("\n¿Confirmar? (s/n): ").strip().lower()
            if r != "s":
                print("Cancelado.")
                return False

        session.execute(text("""
            UPDATE partidos SET numero_partido = :nuevo WHERE id_partido = :id
        """), {"nuevo": ultimo.numero_partido, "id": primero.id_partido})
        session.execute(text("""
            UPDATE partidos SET numero_partido = :nuevo WHERE id_partido = :id
        """), {"nuevo": primero.numero_partido, "id": ultimo.id_partido})
        session.commit()

        print("\n✅ Intercambio hecho. Recargá el bracket en la app.")
        return True
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    ap = argparse.ArgumentParser(description="Intercambiar primer y último cuadro de cuartos")
    ap.add_argument("torneo_id", nargs="?", type=int, default=37, help="ID del torneo (default: 37)")
    ap.add_argument("categoria_id", nargs="?", type=int, default=2, help="ID de la categoría (default: 2)")
    ap.add_argument("-y", "--yes", action="store_true", help="No pedir confirmación")
    args = ap.parse_args()

    print(f"Conectando a DB... (torneo={args.torneo_id}, categoría={args.categoria_id})")
    ok = intercambiar_cuartos(args.torneo_id, args.categoria_id, confirmar=not args.yes)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
