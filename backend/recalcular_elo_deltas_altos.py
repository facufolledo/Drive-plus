"""
Recalcula ELO en partidos donde algún jugador tuvo un delta anormalmente alto
(por ej. +109) por los caps antiguos de 8va/Principiante.
- Encuentra partidos con |delta| > UMBRAL en historial_rating.
- Revierte el ELO (restaura rating_antes, borra historial).
- Reaplica el cálculo con la config actual (caps 50/-25).
Solo partidos de TORNEO (pareja1_id/pareja2_id y resultado_padel).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.config import get_db
from src.models.driveplus_models import Partido, Usuario, HistorialRating
from src.services.elo_service import EloService
from src.services.categoria_service import actualizar_categoria_usuario
from datetime import datetime

load_dotenv()

# Partidos con al menos un delta (en valor absoluto) por encima de este umbral se recalculan
UMBRAL_DELTA = 60


def partidos_con_delta_alto(db: Session) -> list:
    """Partidos que tienen al menos una entrada en historial_rating con |delta| > UMBRAL."""
    rows = db.execute(text("""
        SELECT DISTINCT id_partido
        FROM historial_rating
        WHERE ABS(delta) > :umbral
        ORDER BY id_partido
    """), {'umbral': UMBRAL_DELTA}).fetchall()
    return [r[0] for r in rows]


def es_partido_torneo(partido: Partido) -> bool:
    return bool(
        partido.id_torneo
        and partido.pareja1_id
        and partido.pareja2_id
        and partido.resultado_padel
        and partido.elo_aplicado
    )


def recalcular_partido(db: Session, partido_id: int) -> bool:
    """
    Revierte el ELO del partido y lo vuelve a aplicar con la config actual.
    Devuelve True si se recalculó, False si se saltó (no torneo, sin resultado, etc.).
    """
    partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
    if not partido or not es_partido_torneo(partido):
        return False

    historiales = db.query(HistorialRating).filter(
        HistorialRating.id_partido == partido_id
    ).all()
    if len(historiales) != 4:
        return False

    # Para recalcular en cadena (varios partidos): rating antes = actual - delta
    # así no mezclamos con el rating_antes guardado de cuando se aplicó originalmente
    delta_antes = {h.id_usuario: h.delta for h in historiales}
    usuarios_actuales = {h.id_usuario: db.query(Usuario).filter(Usuario.id_usuario == h.id_usuario).first() for h in historiales}
    rating_antes = {
        uid: (usuarios_actuales[uid].rating or 1200) - delta_antes[uid]
        for uid in delta_antes if usuarios_actuales.get(uid)
    }

    # Parejas
    result1 = db.execute(text(
        "SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :id"
    ), {'id': partido.pareja1_id}).fetchone()
    result2 = db.execute(text(
        "SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :id"
    ), {'id': partido.pareja2_id}).fetchone()
    if not result1 or not result2:
        return False

    pareja1_j1, pareja1_j2 = result1[1], result1[2]
    pareja2_j1, pareja2_j2 = result2[1], result2[2]
    jugadores_ids = [pareja1_j1, pareja1_j2, pareja2_j1, pareja2_j2]

    # partidos_jugados ANTES de este partido (para el cálculo ELO)
    usuarios = {uid: db.query(Usuario).filter(Usuario.id_usuario == uid).first() for uid in jugadores_ids}
    partidos_jugados = {}
    for uid in jugadores_ids:
        u = usuarios.get(uid)
        partidos_jugados[uid] = max(0, (u.partidos_jugados or 0) - 1)

    # Datos para EloService: rating = rating_antes (estado antes de este partido)
    team_a = [
        {'id': pareja1_j1, 'rating': rating_antes.get(pareja1_j1, 1200), 'partidos': partidos_jugados.get(pareja1_j1, 0)},
        {'id': pareja1_j2, 'rating': rating_antes.get(pareja1_j2, 1200), 'partidos': partidos_jugados.get(pareja1_j2, 0)},
    ]
    team_b = [
        {'id': pareja2_j1, 'rating': rating_antes.get(pareja2_j1, 1200), 'partidos': partidos_jugados.get(pareja2_j1, 0)},
        {'id': pareja2_j2, 'rating': rating_antes.get(pareja2_j2, 1200), 'partidos': partidos_jugados.get(pareja2_j2, 0)},
    ]

    resultado = partido.resultado_padel or {}
    sets = resultado.get('sets', [])
    if not sets:
        return False

    # Mapeo pareja1 = equipoA, pareja2 = equipoB (convención frontend)
    jugadores_resultado = resultado.get('jugadores', {})
    jugadores_equipoA = jugadores_resultado.get('equipoA', [])
    ids_pareja1 = {pareja1_j1, pareja1_j2}
    ids_equipoA = {j.get('id') for j in jugadores_equipoA if j.get('id')}
    pareja1_es_equipoA = bool(ids_pareja1.intersection(ids_equipoA)) if jugadores_equipoA else True

    sets_a = sum(1 for s in sets if s.get('ganador') == 'equipoA')
    sets_b = sum(1 for s in sets if s.get('ganador') == 'equipoB')
    games_a = sum(s.get('gamesEquipoA', 0) for s in sets)
    games_b = sum(s.get('gamesEquipoB', 0) for s in sets)

    if pareja1_es_equipoA:
        sets_p1, sets_p2 = sets_a, sets_b
        games_p1, games_p2 = games_a, games_b
        sets_detail = [{'games_a': s.get('gamesEquipoA', 0), 'games_b': s.get('gamesEquipoB', 0)} for s in sets]
    else:
        sets_p1, sets_p2 = sets_b, sets_a
        games_p1, games_p2 = games_b, games_a
        sets_detail = [{'games_a': s.get('gamesEquipoB', 0), 'games_b': s.get('gamesEquipoA', 0)} for s in sets]

    elo = EloService()
    resultado_elo = elo.calculate_match_ratings(
        team_a_players=team_a,
        team_b_players=team_b,
        sets_a=sets_p1,
        sets_b=sets_p2,
        games_a=games_p1,
        games_b=games_p2,
        sets_detail=sets_detail,
        match_type='torneo',
        match_date=partido.fecha or datetime.now()
    )

    deltas_nuevo = {
        pareja1_j1: resultado_elo['team_a']['players'][0]['rating_change'],
        pareja1_j2: resultado_elo['team_a']['players'][1]['rating_change'],
        pareja2_j1: resultado_elo['team_b']['players'][0]['rating_change'],
        pareja2_j2: resultado_elo['team_b']['players'][1]['rating_change'],
    }
    nuevo_rating = {
        pareja1_j1: resultado_elo['team_a']['players'][0]['new_rating'],
        pareja1_j2: resultado_elo['team_a']['players'][1]['new_rating'],
        pareja2_j1: resultado_elo['team_b']['players'][0]['new_rating'],
        pareja2_j2: resultado_elo['team_b']['players'][1]['new_rating'],
    }

    # PASO 1: Revertir (rating = rating_antes calculado, partidos_jugados - 1, borrar historial)
    for h in historiales:
        u = db.query(Usuario).filter(Usuario.id_usuario == h.id_usuario).first()
        if u:
            u.rating = rating_antes.get(h.id_usuario, 1200)
            u.partidos_jugados = max(0, (u.partidos_jugados or 0) - 1)
    db.query(HistorialRating).filter(HistorialRating.id_partido == partido_id).delete()

    # PASO 2: Aplicar nuevo ELO
    for uid in jugadores_ids:
        u = db.query(Usuario).filter(Usuario.id_usuario == uid).first()
        if u:
            r_antes = rating_antes.get(uid, 1200)
            r_nuevo = int(round(nuevo_rating[uid]))
            delta = int(round(deltas_nuevo[uid]))
            u.rating = r_nuevo
            u.partidos_jugados = (u.partidos_jugados or 0) + 1
            actualizar_categoria_usuario(db, u)
            db.add(HistorialRating(
                id_usuario=uid,
                id_partido=partido_id,
                rating_antes=r_antes,
                delta=delta,
                rating_despues=r_nuevo
            ))

    # Log resumen (deltas antes -> después)
    print(f"  Partido {partido_id} (torneo {partido.id_torneo}):")
    for uid in jugadores_ids:
        da = delta_antes.get(uid, 0)
        dn = int(round(deltas_nuevo[uid]))
        if da != dn:
            print(f"    usuario {uid}: delta {da:+d} → {dn:+d}")
    return True


def main():
    db = next(get_db())
    try:
        print("\n" + "=" * 60)
        print("Recalcular ELO en partidos con deltas muy altos (|delta| > {})".format(UMBRAL_DELTA))
        print("=" * 60 + "\n")

        partido_ids = partidos_con_delta_alto(db)
        if not partido_ids:
            print("No hay partidos con |delta| > {} en historial_rating.".format(UMBRAL_DELTA))
            return

        # Ordenar por fecha para mantener consistencia si un jugador tiene varios
        partidos = db.query(Partido).filter(
            Partido.id_partido.in_(partido_ids),
            Partido.fecha.isnot(None)
        ).order_by(Partido.fecha.asc()).all()
        # Incluir los que no tienen fecha al final
        sin_fecha = [p for p in partido_ids if p not in {p.id_partido for p in partidos}]
        orden = [p.id_partido for p in partidos] + sin_fecha

        print("Partidos a procesar (por fecha):", orden, "\n")

        recalc = 0
        for partido_id in orden:
            if recalcular_partido(db, partido_id):
                recalc += 1

        db.commit()
        print("\n" + "=" * 60)
        print("Recalculados: {} partidos.".format(recalc))
        print("=" * 60 + "\n")

    except Exception as e:
        print("\nError:", e)
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
