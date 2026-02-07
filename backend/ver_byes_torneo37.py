"""
Muestra cómo quedarían los BYE en el torneo 37 con el estado ACTUAL de las zonas.
Aunque no se hayan jugado todos los partidos de zona, usa la tabla de posiciones
actual (puntos, sets, games) para ordenar y simular el cuadro de playoffs.

Ejecutar: desde backend con venv activado
  python ver_byes_torneo37.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from src.database.config import get_db
from src.models.torneo_models import TorneoCategoria, TorneoPareja
from src.models.driveplus_models import PerfilUsuario
from src.services.torneo_playoff_service import TorneoPlayoffService

load_dotenv()

TORNEO_ID = 37
CLASIFICADOS_POR_ZONA = 2


def nombre_pareja(db, pareja_id):
    if not pareja_id:
        return None
    pareja = db.query(TorneoPareja).filter(TorneoPareja.id == pareja_id).first()
    if not pareja:
        return f"Pareja #{pareja_id}"
    p1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
    p2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
    n1 = f"{p1.nombre} {p1.apellido}" if p1 else f"J{pareja.jugador1_id}"
    n2 = f"{p2.nombre} {p2.apellido}" if p2 else f"J{pareja.jugador2_id}"
    return f"{n1} / {n2}"


def main():
    db = next(get_db())
    try:
        categorias = db.query(TorneoCategoria).filter(
            TorneoCategoria.torneo_id == TORNEO_ID
        ).order_by(TorneoCategoria.id).all()

        if not categorias:
            print("No hay categorías en el torneo 37.")
            return

        print("\n" + "=" * 70)
        print("BYES TORNEO 37 (según estado actual de zonas)")
        print("=" * 70)

        for cat in categorias:
            clasificados = TorneoPlayoffService._obtener_clasificados_categoria(
                db, TORNEO_ID, cat.id, CLASIFICADOS_POR_ZONA
            )
            n = len(clasificados)
            if n < 2:
                print(f"\n📋 {cat.nombre}: {n} clasificados (se necesitan al menos 2 para playoffs)")
                continue

            bracket_size = TorneoPlayoffService._next_power_of_two(n)
            if bracket_size > 16:
                bracket_size = 16
            num_byes = bracket_size - min(n, 16)

            # Mismo orden y seeds que en generar_playoffs
            clasificados_ordenados = sorted(
                clasificados,
                key=lambda x: (x['posicion'], -x['puntos'], -x['rating'])
            )
            for i, c in enumerate(clasificados_ordenados):
                c['seed'] = i + 1
            clasificados_dict = {c['seed']: c for c in clasificados_ordenados}

            emparejamientos = TorneoPlayoffService._generar_emparejamientos(bracket_size)

            print(f"\n📋 {cat.nombre}")
            print(f"   Clasificados (top {CLASIFICADOS_POR_ZONA} por zona): {n}")
            print(f"   Cuadro: {bracket_size} | BYE: {num_byes}")
            print()

            byes_list = []
            for i, (seed1, seed2) in enumerate(emparejamientos):
                c1 = clasificados_dict.get(seed1)
                c2 = clasificados_dict.get(seed2)
                pareja1_id = c1['pareja_id'] if c1 else None
                pareja2_id = c2['pareja_id'] if c2 else None
                es_bye = (pareja1_id is not None and pareja2_id is None) or (
                    pareja1_id is None and pareja2_id is not None
                )
                if es_bye:
                    seed_con_bye = seed1 if pareja1_id else seed2
                    pareja_id = pareja1_id or pareja2_id
                    nom = nombre_pareja(db, pareja_id)
                    byes_list.append((seed_con_bye, nom, pareja_id))
                partido_n = i + 1
                if es_bye:
                    s = seed1 if pareja1_id else seed2
                    print(f"   Partido {partido_n}: Seed {s} → BYE  ({nombre_pareja(db, pareja1_id or pareja2_id)})")
                else:
                    print(f"   Partido {partido_n}: Seed {seed1} vs Seed {seed2}  ({nombre_pareja(db, pareja1_id)} vs {nombre_pareja(db, pareja2_id)})")

            if byes_list:
                print()
                print("   Quienes tienen BYE (pasan directo a la siguiente ronda):")
                for seed, nom, _ in sorted(byes_list, key=lambda x: x[0]):
                    print(f"      • Seed {seed}: {nom}")

        print("\n" + "=" * 70)
        print("(Orden de zonas y posiciones según tabla actual; puede cambiar al jugar más partidos)")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
