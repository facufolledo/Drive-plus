"""
Script para corregir Matias Vega: ponerlo en Principiante y recalcular ELO
- Matias Vega es Principiante (rating inicial ~800)
- Leo Mena y Carlos Fernandez permanecen en 8va - correcto
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.config import get_db
from src.models.driveplus_models import Partido, Usuario, HistorialRating
from src.models.torneo_models import TorneoPareja
from src.services.elo_service import EloService
from src.services.categoria_service import actualizar_categoria_usuario
from datetime import datetime

load_dotenv()

# Rating Principiante (8va inicial según doc 07-reglas-rating: 800)
RATING_PRINCIPIANTE = 800


def buscar_matias_vega(db: Session) -> Usuario | None:
    """Busca a Matias Vega por nombre/apellido o username"""
    from src.models.driveplus_models import PerfilUsuario
    
    # Buscar por perfil: Matias Vega
    perfil = db.query(PerfilUsuario).filter(
        PerfilUsuario.nombre.ilike('%matias%'),
        PerfilUsuario.apellido.ilike('%vega%')
    ).first()
    
    if perfil:
        return db.query(Usuario).filter(Usuario.id_usuario == perfil.id_usuario).first()
    
    # Fallback: buscar por nombre_usuario
    return db.query(Usuario).filter(
        Usuario.nombre_usuario.ilike('%vega%')
    ).first()


def encontrar_partidos_matias(db: Session, matias_id: int) -> list:
    """Encuentra partidos del torneo 37 donde jugó Matias Vega"""
    partidos_ids = []
    
    # Matias puede estar en torneos_parejas como jugador1 o jugador2
    parejas = db.execute(text("""
        SELECT id, torneo_id, jugador1_id, jugador2_id 
        FROM torneos_parejas 
        WHERE jugador1_id = :uid OR jugador2_id = :uid
    """), {'uid': matias_id}).fetchall()
    
    for row in parejas:
        pareja_id = row[0]
        torneo_id = row[1]
        
        if torneo_id == 37:
            # Buscar partidos donde esta pareja jugó
            partidos = db.query(Partido).filter(
                Partido.id_torneo == 37,
                Partido.elo_aplicado == True,
                (Partido.pareja1_id == pareja_id) | (Partido.pareja2_id == pareja_id)
            ).all()
            for p in partidos:
                partidos_ids.append(p.id_partido)
    
    return list(set(partidos_ids))


def corregir_matias_vega():
    """Corrige rating de Matias Vega a 7ma y recalcula ELO en sus partidos"""
    db = next(get_db())
    
    try:
        print("\n" + "="*70)
        print("🔧 CORRECCIÓN: Matias Vega → Principiante")
        print("="*70 + "\n")
        
        # 1. Buscar Matias Vega
        matias = buscar_matias_vega(db)
        if not matias:
            print("❌ Matias Vega no encontrado")
            return
        
        print(f"✅ Matias Vega encontrado: ID {matias.id_usuario}")
        print(f"   Username: {matias.nombre_usuario}")
        print(f"   Rating actual: {matias.rating}")
        print()
        
        # 2. Encontrar partidos donde jugó
        partidos_ids = encontrar_partidos_matias(db, matias.id_usuario)
        if not partidos_ids:
            print("⚠️  No se encontraron partidos del torneo 37 con ELO aplicado")
            print("   (Matias puede no haber jugado aún, o los partidos no tienen resultado)")
            return
        
        print(f"📋 Partidos a recalcular: {partidos_ids}\n")
        
        for partido_id in partidos_ids:
            partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
            if not partido or not partido.resultado_padel:
                continue
            
            print(f"--- Partido {partido_id} ---")
            
            # Obtener parejas
            result1 = db.execute(text(
                "SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :id"
            ), {'id': partido.pareja1_id}).fetchone()
            result2 = db.execute(text(
                "SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :id"
            ), {'id': partido.pareja2_id}).fetchone()
            
            if not result1 or not result2:
                print("  ❌ Parejas no encontradas")
                continue
            
            pareja1_j1, pareja1_j2 = result1[1], result1[2]
            pareja2_j1, pareja2_j2 = result2[1], result2[2]
            
            # Obtener historial actual para ratings ANTES del partido
            historiales = db.query(HistorialRating).filter(
                HistorialRating.id_partido == partido_id
            ).all()
            
            rating_antes = {h.id_usuario: h.rating_antes for h in historiales}
            
            # Para Matias: usar rating 7ma. Para los demás: usar su rating_antes
            def rating_para_elo(uid: int) -> int:
                if uid == matias.id_usuario:
                    return RATING_PRINCIPIANTE
                return rating_antes.get(uid, 1200)
            
            # Obtener partidos_jugados para cada jugador (antes de este partido)
            jugadores_ids = [pareja1_j1, pareja1_j2, pareja2_j1, pareja2_j2]
            usuarios = {uid: db.query(Usuario).filter(Usuario.id_usuario == uid).first() for uid in jugadores_ids}
            partidos_jugados = {uid: (u.partidos_jugados or 1) - 1 for uid, u in usuarios.items() if u}
            for uid in jugadores_ids:
                if uid not in partidos_jugados:
                    partidos_jugados[uid] = 0
            
            team_a = [
                {'id': pareja1_j1, 'rating': rating_para_elo(pareja1_j1), 'partidos': partidos_jugados.get(pareja1_j1, 0)},
                {'id': pareja1_j2, 'rating': rating_para_elo(pareja1_j2), 'partidos': partidos_jugados.get(pareja1_j2, 0)},
            ]
            team_b = [
                {'id': pareja2_j1, 'rating': rating_para_elo(pareja2_j1), 'partidos': partidos_jugados.get(pareja2_j1, 0)},
                {'id': pareja2_j2, 'rating': rating_para_elo(pareja2_j2), 'partidos': partidos_jugados.get(pareja2_j2, 0)},
            ]
            
            # Resultado: pareja1 = equipoA, pareja2 = equipoB (convención frontend)
            sets = partido.resultado_padel.get('sets', [])
            sets_pareja1 = sum(1 for s in sets if s.get('ganador') == 'equipoA')
            sets_pareja2 = sum(1 for s in sets if s.get('ganador') == 'equipoB')
            games_pareja1 = sum(s.get('gamesEquipoA', 0) for s in sets)
            games_pareja2 = sum(s.get('gamesEquipoB', 0) for s in sets)
            sets_detail = [{'games_a': s.get('gamesEquipoA', 0), 'games_b': s.get('gamesEquipoB', 0)} for s in sets]
            
            # Calcular ELO correcto
            elo = EloService()
            resultado_elo = elo.calculate_match_ratings(
                team_a_players=team_a,
                team_b_players=team_b,
                sets_a=sets_pareja1,
                sets_b=sets_pareja2,
                games_a=games_pareja1,
                games_b=games_pareja2,
                sets_detail=sets_detail,
                match_type='torneo',
                match_date=partido.fecha or datetime.now()
            )
            
            # Mapear deltas: team_a -> pareja1, team_b -> pareja2
            deltas = {
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
            
            # Mostrar cambio para Matias
            delta_matias = int(round(deltas[matias.id_usuario]))
            rating_matias_antes = rating_para_elo(matias.id_usuario)
            rating_matias_nuevo = int(round(nuevo_rating[matias.id_usuario]))
            
            print(f"  Matias Vega: {rating_matias_antes} → {rating_matias_nuevo} ({delta_matias:+d})")
            
            # PASO 1: Revertir ELO actual (restaurar todos al rating_antes, borrar historial)
            for h in historiales:
                u = db.query(Usuario).filter(Usuario.id_usuario == h.id_usuario).first()
                if u:
                    u.rating = h.rating_antes
                    u.partidos_jugados = max(0, (u.partidos_jugados or 0) - 1)
            
            db.query(HistorialRating).filter(HistorialRating.id_partido == partido_id).delete()
            
            # PASO 2: Aplicar ELO correcto (con Matias en Principiante)
            for uid in jugadores_ids:
                u = db.query(Usuario).filter(Usuario.id_usuario == uid).first()
                if u:
                    r_antes = rating_para_elo(uid)
                    r_nuevo = int(round(nuevo_rating[uid]))
                    delta = int(round(deltas[uid]))
                    
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
            
            partido.elo_aplicado = True
            print(f"  ✅ ELO recalculado y aplicado")
        
        db.commit()
        
        # Actualizar id_categoria de Matias a Principiante
        db.refresh(matias)
        actualizar_categoria_usuario(db, matias)
        db.commit()
        
        print("\n" + "="*70)
        print("✅ CORRECCIÓN COMPLETADA")
        print("="*70)
        print(f"\nMatias Vega: rating actualizado a Principiante ({RATING_PRINCIPIANTE})")
        print("ELO recalculado en sus partidos del torneo 37.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    corregir_matias_vega()
