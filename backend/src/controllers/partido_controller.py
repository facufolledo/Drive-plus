from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database.config import get_db
from ..models.driveplus_models import Partido, PartidoJugador, ResultadoPartido, Usuario, Club, HistorialRating, PerfilUsuario, Categoria
from ..schemas.partido import PartidoCreate, PartidoResponse, PartidoCompleto, ResultadoCreate
from ..auth.auth_utils import get_current_user
from ..services.elo_service import EloService
from ..services.categoria_service import actualizar_categoria_usuario

router = APIRouter(prefix="/partidos", tags=["Partidos"])

@router.post("/", response_model=PartidoResponse)
async def crear_partido(
    partido_data: PartidoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo partido"""
    
    # Verificar que el usuario esté en la lista de jugadores
    if current_user.id_usuario not in partido_data.jugadores:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El creador debe ser uno de los jugadores"
        )
    
    # Verificar que haya 4 jugadores
    if len(partido_data.jugadores) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe haber exactamente 4 jugadores"
        )
    
    # Verificar que los equipos sean válidos (1 o 2)
    if not all(equipo in [1, 2] for equipo in partido_data.equipos):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los equipos deben ser 1 o 2"
        )
    
    try:
        # Crear el partido
        db_partido = Partido(
            fecha=partido_data.fecha,
            estado="pendiente",
            id_creador=current_user.id_usuario,
            id_club=partido_data.id_club
        )
        
        db.add(db_partido)
        db.flush()  # Para obtener el ID del partido
        
        # Agregar jugadores al partido
        for i, jugador_id in enumerate(partido_data.jugadores):
            db_jugador = PartidoJugador(
                id_partido=db_partido.id_partido,
                id_usuario=jugador_id,
                equipo=partido_data.equipos[i]
            )
            db.add(db_jugador)
        
        db.commit()
        db.refresh(db_partido)
        
        # Retornar partido creado
        return PartidoResponse(
            id_partido=db_partido.id_partido,
            fecha=db_partido.fecha,
            estado=db_partido.estado,
            id_creador=db_partido.id_creador,
            creado_en=db_partido.creado_en,
            id_club=db_partido.id_club,
            jugadores=[]
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear partido: {str(e)}"
        )

@router.get("/", response_model=List[PartidoCompleto])
async def listar_partidos(
    estado: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Listar partidos con filtros opcionales"""
    
    query = db.query(Partido)
    
    if estado:
        query = query.filter(Partido.estado == estado)
    
    partidos = query.order_by(Partido.fecha.desc()).limit(limit).all()
    
    if not partidos:
        return []
    
    partido_ids = [p.id_partido for p in partidos]
    # Batch: jugadores, resultados, clubs, creadores (evitar N+1)
    todos_jugadores = db.query(PartidoJugador).filter(PartidoJugador.id_partido.in_(partido_ids)).all()
    resultados = db.query(ResultadoPartido).filter(ResultadoPartido.id_partido.in_(partido_ids)).all()
    club_ids = list({p.id_club for p in partidos if p.id_club})
    creador_ids = list({p.id_creador for p in partidos if p.id_creador})
    clubs = db.query(Club).filter(Club.id_club.in_(club_ids)).all() if club_ids else []
    creadores = db.query(Usuario).filter(Usuario.id_usuario.in_(creador_ids)).all() if creador_ids else []
    
    resultados_dict = {r.id_partido: r for r in resultados}
    clubs_dict = {c.id_club: c for c in clubs}
    creadores_dict = {u.id_usuario: u for u in creadores}
    
    partidos_completos = []
    for partido in partidos:
        resultado = resultados_dict.get(partido.id_partido)
        club = clubs_dict.get(partido.id_club) if partido.id_club else None
        creador = creadores_dict.get(partido.id_creador) if partido.id_creador else None
        partidos_completos.append(PartidoCompleto(
            id_partido=partido.id_partido,
            fecha=partido.fecha,
            estado=partido.estado,
            id_creador=partido.id_creador,
            creado_en=partido.creado_en,
            id_club=partido.id_club,
            jugadores=[],
            resultado=resultado,
            club=club,
            creador={
                "id_usuario": creador.id_usuario,
                "nombre_usuario": creador.nombre_usuario
            } if creador else {}
        ))
    
    return partidos_completos

@router.get("/{partido_id}", response_model=PartidoCompleto)
async def obtener_partido(
    partido_id: int,
    db: Session = Depends(get_db)
):
    """Obtener un partido específico con todos sus datos"""
    
    partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
    
    if not partido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partido no encontrado"
        )
    
    # Obtener jugadores
    jugadores = db.query(PartidoJugador).filter(
        PartidoJugador.id_partido == partido.id_partido
    ).all()
    
    # Obtener resultado si existe
    resultado = db.query(ResultadoPartido).filter(
        ResultadoPartido.id_partido == partido.id_partido
    ).first()
    
    # Obtener club si existe
    club = None
    if partido.id_club:
        club = db.query(Club).filter(Club.id_club == partido.id_club).first()
    
    # Obtener creador
    creador = db.query(Usuario).filter(Usuario.id_usuario == partido.id_creador).first()
    
    return PartidoCompleto(
        id_partido=partido.id_partido,
        fecha=partido.fecha,
        estado=partido.estado,
        id_creador=partido.id_creador,
        creado_en=partido.creado_en,
        id_club=partido.id_club,
        jugadores=[],
        resultado=resultado,
        club=club,
        creador={
            "id_usuario": creador.id_usuario,
            "nombre_usuario": creador.nombre_usuario
        } if creador else {}
    )

@router.post("/{partido_id}/resultado")
async def reportar_resultado(
    partido_id: int,
    resultado_data: ResultadoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reportar resultado de un partido (sin calcular Elo aún)"""
    
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
    
    if not partido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partido no encontrado"
        )
    
    # Verificar que el partido esté en estado "pendiente"
    if partido.estado != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden reportar resultados de partidos pendientes"
        )
    
    # Verificar que el usuario sea uno de los jugadores
    jugador_partido = db.query(PartidoJugador).filter(
        PartidoJugador.id_partido == partido_id,
        PartidoJugador.id_usuario == current_user.id_usuario
    ).first()
    
    if not jugador_partido:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los jugadores del partido pueden reportar resultados"
        )
    
    try:
        # Crear resultado
        db_resultado = ResultadoPartido(
            id_partido=partido_id,
            id_reportador=current_user.id_usuario,
            sets_eq1=resultado_data.sets_eq1,
            sets_eq2=resultado_data.sets_eq2,
            detalle_sets=resultado_data.detalle_sets,
            desenlace=resultado_data.desenlace
        )
        
        db.add(db_resultado)
        
        # Cambiar estado del partido a "reportado"
        partido.estado = "reportado"
        
        db.commit()
        
        return {
            "message": "Resultado reportado exitosamente. El equipo rival debe confirmarlo para calcular el ranking Elo.",
            "estado": "reportado",
            "resultado": {
                "sets_equipo1": resultado_data.sets_eq1,
                "sets_equipo2": resultado_data.sets_eq2,
                "desenlace": resultado_data.desenlace,
                "reportado_por": current_user.nombre_usuario
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reportar resultado: {str(e)}"
        )
        
        return {
            "message": "Resultado reportado exitosamente y ranking Elo avanzado actualizado (estado: reportado)",
            "equipo1": {
                "sets": resultado_data.sets_eq1,
                "rating_antes": nuevos_ratings['team_a']['old_rating'],
                "rating_despues": nuevos_ratings['team_a']['new_rating'],
                "cambio": nuevos_ratings['team_a']['rating_change'],
                "jugadores": [
                    {
                        "rating_antes": player['old_rating'],
                        "rating_despues": player['new_rating'],
                        "cambio": player['rating_change']
                    }
                    for player in nuevos_ratings['team_a']['players']
                ]
            },
            "equipo2": {
                "sets": resultado_data.sets_eq2,
                "rating_antes": nuevos_ratings['team_b']['old_rating'],
                "rating_despues": nuevos_ratings['team_b']['new_rating'],
                "cambio": nuevos_ratings['team_b']['rating_change'],
                "jugadores": [
                    {
                        "rating_antes": player['old_rating'],
                        "rating_despues": player['new_rating'],
                        "cambio": player['rating_change']
                    }
                    for player in nuevos_ratings['team_b']['players']
                ]
            },
            "detalles_elo": {
                "expectativa_equipo1": nuevos_ratings['match_details']['expected_a'],
                "expectativa_equipo2": nuevos_ratings['match_details']['expected_b'],
                "puntuacion_real_equipo1": nuevos_ratings['match_details']['actual_score_a'],
                "puntuacion_real_equipo2": nuevos_ratings['match_details']['actual_score_b'],
                "multiplicador_sets": nuevos_ratings['match_details']['sets_multiplier'],
                "factor_k_equipo1": nuevos_ratings['match_details']['team_a_k'],
                "factor_k_equipo2": nuevos_ratings['match_details']['team_b_k'],
                "suavizador_equipo1": nuevos_ratings['match_details']['loss_softener_a'],
                "suavizador_equipo2": nuevos_ratings['match_details']['loss_softener_b'],
                "caps_equipo1": nuevos_ratings['match_details']['caps_a'],
                "caps_equipo2": nuevos_ratings['match_details']['caps_b']
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reportar resultado: {str(e)}"
        )

@router.post("/{partido_id}/confirmar")
async def confirmar_resultado(
    partido_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirmar resultado reportado (sin calcular Elo aún)"""
    
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
    
    if not partido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partido no encontrado"
        )
    
    # Verificar que el partido esté en estado "reportado"
    if partido.estado != "reportado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden confirmar resultados de partidos reportados"
        )
    
    # Verificar que el usuario sea del equipo rival (no del que reportó)
    resultado = db.query(ResultadoPartido).filter(
        ResultadoPartido.id_partido == partido_id
    ).first()
    
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró resultado para este partido"
        )
    
    # Verificar que el usuario NO sea el que reportó el resultado
    if resultado.id_reportador == current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes confirmar tu propio resultado reportado"
        )
    
    # Verificar que el usuario sea uno de los jugadores del partido
    jugador_partido = db.query(PartidoJugador).filter(
        PartidoJugador.id_partido == partido_id,
        PartidoJugador.id_usuario == current_user.id_usuario
    ).first()
    
    if not jugador_partido:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los jugadores del partido pueden confirmar resultados"
        )
    
    try:
        # Solo cambiar estado del partido a "confirmado"
        partido.estado = "confirmado"
        
        db.commit()
        
        return {
            "message": "Resultado confirmado exitosamente. Ahora se puede calcular el ranking Elo.",
            "estado": "confirmado",
            "resultado": {
                "sets_equipo1": resultado.sets_eq1,
                "sets_equipo2": resultado.sets_eq2,
                "desenlace": resultado.desenlace,
                "confirmado_por": current_user.nombre_usuario
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar resultado: {str(e)}"
        )

@router.post("/{partido_id}/calcular-elo")
async def calcular_elo_partido(
    partido_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calcular ranking Elo para un partido confirmado"""
    
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
    
    if not partido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partido no encontrado"
        )
    
    # Verificar que el partido esté en estado "confirmado"
    if partido.estado != "confirmado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede calcular Elo para partidos confirmados"
        )
    
    # Verificar que el usuario sea uno de los jugadores del partido
    jugador_partido = db.query(PartidoJugador).filter(
        PartidoJugador.id_partido == partido_id,
        PartidoJugador.id_usuario == current_user.id_usuario
    ).first()
    
    if not jugador_partido:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los jugadores del partido pueden calcular Elo"
        )
    
    # Verificar que no se haya calculado Elo ya
    historial_existente = db.query(HistorialRating).filter(
        HistorialRating.id_partido == partido_id
    ).first()
    
    if historial_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ranking Elo ya fue calculado para este partido"
        )
    
    try:
        # Obtener resultado del partido
        resultado = db.query(ResultadoPartido).filter(
            ResultadoPartido.id_partido == partido_id
        ).first()
        
        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró resultado para este partido"
            )
        
        # Obtener todos los jugadores del partido
        jugadores_partido = db.query(PartidoJugador).filter(
            PartidoJugador.id_partido == partido_id
        ).all()
        
        if len(jugadores_partido) != 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El partido debe tener exactamente 4 jugadores"
            )
        
        # Separar jugadores por equipos
        equipo1 = [j for j in jugadores_partido if j.equipo == 1]
        equipo2 = [j for j in jugadores_partido if j.equipo == 2]
        
        if len(equipo1) != 2 or len(equipo2) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cada equipo debe tener exactamente 2 jugadores"
            )
        
        # Obtener información de los jugadores (batch, evitar N+1)
        ids_jugadores = [j.id_usuario for j in jugadores_partido]
        usuarios = db.query(Usuario).filter(Usuario.id_usuario.in_(ids_jugadores)).all()
        usuarios_dict = {u.id_usuario: u for u in usuarios}
        jugadores_info = {}
        for jugador in jugadores_partido:
            usuario = usuarios_dict.get(jugador.id_usuario)
            if usuario:
                jugadores_info[jugador.id_usuario] = {
                    'usuario': usuario,
                    'equipo': jugador.equipo
                }
        
        # CALCULAR RANKING ELO AVANZADO
        elo_service = EloService()
        
        # Preparar datos para el algoritmo Elo avanzado
        equipo1_players = [
            {
                "rating": jugadores_info[j.id_usuario]['usuario'].rating,
                "partidos": jugadores_info[j.id_usuario]['usuario'].partidos_jugados
            }
            for j in equipo1
        ]
        
        equipo2_players = [
            {
                "rating": jugadores_info[j.id_usuario]['usuario'].rating,
                "partidos": jugadores_info[j.id_usuario]['usuario'].partidos_jugados
            }
            for j in equipo2
        ]
        
        # Calcular games totales si están disponibles en detalle_sets
        games_equipo1 = 0
        games_equipo2 = 0
        
        if resultado.detalle_sets:
            for set_result in resultado.detalle_sets:
                if isinstance(set_result, str) and '-' in set_result:
                    try:
                        games1, games2 = map(int, set_result.split('-'))
                        games_equipo1 += games1
                        games_equipo2 += games2
                    except (ValueError, AttributeError):
                        pass  # Si no se puede parsear, usar 0
        
        # MAPEAR CORRECTAMENTE EQUIPOS PARA ELO (FIX CRÍTICO)
        # Problema: equipo1/equipo2 != equipoA/equipoB necesariamente
        # Solución: Determinar correspondencia basándose en jugadores
        
        # Obtener información de jugadores por equipo del resultado JSON
        resultado_json = partido.resultado_padel or {}
        jugadores_resultado = resultado_json.get('jugadores', {})
        jugadores_equipoA = jugadores_resultado.get('equipoA', [])
        jugadores_equipoB = jugadores_resultado.get('equipoB', [])
        
        # Determinar si equipo1 corresponde a equipoA o equipoB
        equipo1_es_equipoA = False
        
        if jugadores_equipoA and equipo1:
            # Verificar si algún jugador de equipo1 está en equipoA
            ids_equipo1 = {j.id_usuario for j in equipo1}
            ids_equipoA = {j.get('id') for j in jugadores_equipoA if j.get('id')}
            equipo1_es_equipoA = bool(ids_equipo1.intersection(ids_equipoA))
        
        # Asignar sets correctamente según la correspondencia
        if equipo1_es_equipoA:
            # equipo1 = equipoA, equipo2 = equipoB
            sets_equipo1 = resultado.sets_eq1  # sets de equipoA
            sets_equipo2 = resultado.sets_eq2  # sets de equipoB
            games_equipo1_corregido = games_equipo1
            games_equipo2_corregido = games_equipo2
        else:
            # equipo1 = equipoB, equipo2 = equipoA (INVERTIDO)
            sets_equipo1 = resultado.sets_eq2  # sets de equipoB
            sets_equipo2 = resultado.sets_eq1  # sets de equipoA  
            games_equipo1_corregido = games_equipo2
            games_equipo2_corregido = games_equipo1
        
        # Calcular nuevos ratings usando el algoritmo Elo avanzado (CORREGIDO)
        nuevos_ratings = elo_service.calculate_match_ratings(
            team_a_players=equipo1_players,
            team_b_players=equipo2_players,
            sets_a=sets_equipo1,  # Ahora corresponde correctamente a equipo1
            sets_b=sets_equipo2,  # Ahora corresponde correctamente a equipo2
            games_a=games_equipo1_corregido,
            games_b=games_equipo2_corregido,
            desenlace=resultado.desenlace
        )
        
        # Actualizar ratings de todos los jugadores
        for jugador in jugadores_partido:
            usuario = jugadores_info[jugador.id_usuario]['usuario']
            equipo = jugador.equipo  # Corregido: usar jugador.equipo directamente
            
            # Encontrar el índice del jugador en su equipo (0 o 1)
            equipo_jugadores = equipo1 if equipo == 1 else equipo2
            jugador_index = next(i for i, j in enumerate(equipo_jugadores) if j.id_usuario == jugador.id_usuario)
            
            # Obtener datos del nuevo rating
            if equipo == 1:
                player_data = nuevos_ratings['team_a']['players'][jugador_index]
            else:
                player_data = nuevos_ratings['team_b']['players'][jugador_index]
            
            rating_antes = usuario.rating
            rating_despues = player_data['new_rating']
            delta = player_data['rating_change']
            
            # Actualizar usuario
            usuario.rating = int(rating_despues)
            usuario.partidos_jugados += 1
            
            # Actualizar categoría según el nuevo rating
            actualizar_categoria_usuario(db, usuario)
            
            # Crear registro en historial de rating
            historial = HistorialRating(
                id_usuario=usuario.id_usuario,
                id_partido=partido_id,
                rating_antes=rating_antes,
                delta=int(delta),  # Convertir delta a entero
                rating_despues=int(rating_despues)
            )
            db.add(historial)
        
        db.commit()
        
        return {
            "message": "Ranking Elo avanzado calculado y aplicado exitosamente",
            "equipo1": {
                "sets": resultado.sets_eq1,
                "rating_antes": nuevos_ratings['team_a']['old_rating'],
                "rating_despues": nuevos_ratings['team_a']['new_rating'],
                "cambio": nuevos_ratings['team_a']['rating_change'],
                "jugadores": [
                    {
                        "rating_antes": player['old_rating'],
                        "rating_despues": player['new_rating'],
                        "cambio": player['rating_change']
                    }
                    for player in nuevos_ratings['team_a']['players']
                ]
            },
            "equipo2": {
                "sets": resultado.sets_eq2,
                "rating_antes": nuevos_ratings['team_b']['old_rating'],
                "rating_despues": nuevos_ratings['team_b']['new_rating'],
                "cambio": nuevos_ratings['team_b']['rating_change'],
                "jugadores": [
                    {
                        "rating_antes": player['old_rating'],
                        "rating_despues": player['new_rating'],
                        "cambio": player['rating_change']
                    }
                    for player in nuevos_ratings['team_b']['players']
                ]
            },
            "detalles_elo": {
                "expectativa_equipo1": nuevos_ratings['match_details']['expected_a'],
                "expectativa_equipo2": nuevos_ratings['match_details']['expected_b'],
                "puntuacion_real_equipo1": nuevos_ratings['match_details']['actual_score_a'],
                "puntuacion_real_equipo2": nuevos_ratings['match_details']['actual_score_b'],
                "multiplicador_sets": nuevos_ratings['match_details']['sets_multiplier'],
                "factor_k_equipo1": nuevos_ratings['match_details']['team_a_k'],
                "factor_k_equipo2": nuevos_ratings['match_details']['team_b_k'],
                "suavizador_equipo1": nuevos_ratings['match_details']['loss_softener_a'],
                "suavizador_equipo2": nuevos_ratings['match_details']['loss_softener_b'],
                "caps_equipo1": nuevos_ratings['match_details']['caps_a'],
                "caps_equipo2": nuevos_ratings['match_details']['caps_b']
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular Elo: {str(e)}"
        )

@router.get("/usuario/{usuario_id}")
async def partidos_usuario(
    usuario_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtener partidos de un usuario específico con historial completo (solo confirmados con resultado) - OPTIMIZADO"""
    
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    from sqlalchemy import and_, or_, text
    
    # 1. Obtener partidos amistosos (usando partido_jugadores)
    partidos_amistosos = db.query(Partido).join(
        PartidoJugador, Partido.id_partido == PartidoJugador.id_partido
    ).filter(
        and_(
            PartidoJugador.id_usuario == usuario_id,
            Partido.estado.in_(["confirmado", "finalizado"]),
            or_(Partido.tipo == "amistoso", Partido.tipo.is_(None))
        )
    ).all()
    
    # 2. Obtener partidos de torneo donde el usuario REALMENTE participó
    # Usar historial_rating que es la fuente de verdad de participación
    partidos_torneo_ids = db.execute(text("""
        SELECT DISTINCT hr.id_partido 
        FROM historial_rating hr
        JOIN partidos p ON hr.id_partido = p.id_partido
        WHERE hr.id_usuario = :uid
        AND p.tipo = 'torneo'
        AND p.estado IN ('confirmado', 'finalizado')
    """), {'uid': usuario_id}).fetchall()
    
    torneo_ids = [p[0] for p in partidos_torneo_ids]
    
    partidos_torneo = []
    if torneo_ids:
        partidos_torneo = db.query(Partido).filter(
            Partido.id_partido.in_(torneo_ids)
        ).all()
    
    # Combinar y ordenar por fecha
    partidos = partidos_amistosos + partidos_torneo
    partidos = sorted(partidos, key=lambda p: p.fecha or p.creado_en, reverse=True)[:limit]
    
    if not partidos:
        return []
    
    partido_ids = [p.id_partido for p in partidos]
    
    # OPTIMIZACIÓN: Cargar todos los datos necesarios de una vez
    # Obtener todos los jugadores de todos los partidos en una sola consulta
    todos_jugadores = db.query(PartidoJugador).filter(
        PartidoJugador.id_partido.in_(partido_ids)
    ).all()
    
    # Agrupar jugadores por partido
    jugadores_por_partido = {}
    usuario_ids = set()
    for jugador in todos_jugadores:
        if jugador.id_partido not in jugadores_por_partido:
            jugadores_por_partido[jugador.id_partido] = []
        jugadores_por_partido[jugador.id_partido].append(jugador)
        usuario_ids.add(jugador.id_usuario)
    
    # Obtener todos los usuarios y perfiles en una sola consulta
    usuarios_dict = {u.id_usuario: u for u in db.query(Usuario).filter(Usuario.id_usuario.in_(usuario_ids)).all()}
    perfiles_dict = {p.id_usuario: p for p in db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario.in_(usuario_ids)).all()}
    
    # Obtener todos los resultados en una sola consulta
    resultados_dict = {r.id_partido: r for r in db.query(ResultadoPartido).filter(ResultadoPartido.id_partido.in_(partido_ids)).all()}
    
    # Obtener todo el historial de rating en una sola consulta
    historial_dict = {h.id_partido: h for h in db.query(HistorialRating).filter(
        and_(
            HistorialRating.id_partido.in_(partido_ids),
            HistorialRating.id_usuario == usuario_id
        )
    ).all()}
    
    # Obtener IDs de clubs únicos
    club_ids = [p.id_club for p in partidos if p.id_club]
    clubs_dict = {}
    if club_ids:
        clubs_dict = {c.id_club: c for c in db.query(Club).filter(Club.id_club.in_(club_ids)).all()}
    
    # Obtener categorías de los partidos de torneo
    from src.models.torneo_models import TorneoCategoria
    categoria_ids = [p.categoria_id for p in partidos if p.categoria_id]
    categorias_dict = {}
    if categoria_ids:
        categorias_dict = {c.id: c for c in db.query(TorneoCategoria).filter(TorneoCategoria.id.in_(categoria_ids)).all()}
    
    # Pre-cargar datos de parejas de torneo
    parejas_torneo_dict = {}
    pareja_ids_torneo = set()
    for partido in partidos:
        if partido.tipo == 'torneo':
            if partido.pareja1_id:
                pareja_ids_torneo.add(partido.pareja1_id)
            if partido.pareja2_id:
                pareja_ids_torneo.add(partido.pareja2_id)
    
    if pareja_ids_torneo:
        # Convertir a lista para la consulta
        pareja_ids_list = list(pareja_ids_torneo)
        parejas_data = db.execute(text("""
            SELECT id, jugador1_id, jugador2_id FROM torneos_parejas WHERE id = ANY(:ids)
        """), {'ids': pareja_ids_list}).fetchall()
        for p in parejas_data:
            parejas_torneo_dict[p[0]] = {'jugador1_id': p[1], 'jugador2_id': p[2]}
            usuario_ids.add(p[1])
            usuario_ids.add(p[2])
        
        # Recargar usuarios y perfiles con los nuevos IDs
        usuarios_dict = {u.id_usuario: u for u in db.query(Usuario).filter(Usuario.id_usuario.in_(usuario_ids)).all()}
        perfiles_dict = {p.id_usuario: p for p in db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario.in_(usuario_ids)).all()}
    
    # Construir respuesta completa
    partidos_completos = []
    for partido in partidos:
        jugadores_info = []
        
        if partido.tipo == 'torneo':
            # Para partidos de torneo, obtener jugadores de las parejas
            pareja1 = parejas_torneo_dict.get(partido.pareja1_id)
            pareja2 = parejas_torneo_dict.get(partido.pareja2_id)
            
            if pareja1:
                for jid in [pareja1['jugador1_id'], pareja1['jugador2_id']]:
                    usuario_jugador = usuarios_dict.get(jid)
                    perfil_jugador = perfiles_dict.get(jid)
                    if usuario_jugador:
                        jugadores_info.append({
                            "id_usuario": usuario_jugador.id_usuario,
                            "nombre_usuario": usuario_jugador.nombre_usuario,
                            "nombre": perfil_jugador.nombre if perfil_jugador else "",
                            "apellido": perfil_jugador.apellido if perfil_jugador else "",
                            "equipo": 1,
                            "rating": usuario_jugador.rating
                        })
            
            if pareja2:
                for jid in [pareja2['jugador1_id'], pareja2['jugador2_id']]:
                    usuario_jugador = usuarios_dict.get(jid)
                    perfil_jugador = perfiles_dict.get(jid)
                    if usuario_jugador:
                        jugadores_info.append({
                            "id_usuario": usuario_jugador.id_usuario,
                            "nombre_usuario": usuario_jugador.nombre_usuario,
                            "nombre": perfil_jugador.nombre if perfil_jugador else "",
                            "apellido": perfil_jugador.apellido if perfil_jugador else "",
                            "equipo": 2,
                            "rating": usuario_jugador.rating
                        })
        else:
            # Para partidos amistosos, usar partido_jugadores
            jugadores = jugadores_por_partido.get(partido.id_partido, [])
            for jugador in jugadores:
                usuario_jugador = usuarios_dict.get(jugador.id_usuario)
                perfil_jugador = perfiles_dict.get(jugador.id_usuario)
                
                if usuario_jugador:
                    jugadores_info.append({
                        "id_usuario": usuario_jugador.id_usuario,
                        "nombre_usuario": usuario_jugador.nombre_usuario,
                        "nombre": perfil_jugador.nombre if perfil_jugador else "",
                        "apellido": perfil_jugador.apellido if perfil_jugador else "",
                        "equipo": jugador.equipo,
                        "rating": usuario_jugador.rating
                    })
        
        # Obtener resultado - diferente según tipo de partido
        resultado = resultados_dict.get(partido.id_partido)
        
        # Formatear resultado para incluir detalle_sets correctamente
        resultado_dict = None
        
        # Para partidos de torneo, el resultado está en resultado_padel (JSON)
        if partido.tipo == 'torneo' and partido.resultado_padel:
            resultado_padel = partido.resultado_padel
            sets = resultado_padel.get('sets', [])
            
            # Contar sets ganados
            sets_eq1 = sum(1 for s in sets if s.get('ganador') == 'equipoA')
            sets_eq2 = sum(1 for s in sets if s.get('ganador') == 'equipoB')
            
            # Normalizar detalle_sets
            detalle_sets_normalizado = []
            for idx, set_data in enumerate(sets, 1):
                detalle_sets_normalizado.append({
                    "set": idx,
                    "juegos_eq1": set_data.get('gamesEquipoA', 0),
                    "juegos_eq2": set_data.get('gamesEquipoB', 0),
                    "tiebreak_eq1": set_data.get('tiebreakEquipoA'),
                    "tiebreak_eq2": set_data.get('tiebreakEquipoB')
                })
            
            resultado_dict = {
                "id_partido": partido.id_partido,
                "sets_eq1": sets_eq1,
                "sets_eq2": sets_eq2,
                "detalle_sets": detalle_sets_normalizado,
                "confirmado": True,
                "desenlace": "normal"
            }
        elif resultado:
            # Normalizar detalle_sets a formato consistente
            detalle_sets_normalizado = []
            if resultado.detalle_sets and isinstance(resultado.detalle_sets, list):
                for idx, set_data in enumerate(resultado.detalle_sets, 1):
                    # Formato 1: {'games_eq1': 6, 'games_eq2': 4}
                    if 'games_eq1' in set_data and 'games_eq2' in set_data:
                        detalle_sets_normalizado.append({
                            "set": idx,
                            "juegos_eq1": set_data['games_eq1'],
                            "juegos_eq2": set_data['games_eq2'],
                            "tiebreak_eq1": set_data.get('tiebreak_eq1'),
                            "tiebreak_eq2": set_data.get('tiebreak_eq2')
                        })
                    # Formato 2: {'puntos_eq1': 6, 'puntos_eq2': 4, 'set_numero': 1}
                    elif 'puntos_eq1' in set_data and 'puntos_eq2' in set_data:
                        detalle_sets_normalizado.append({
                            "set": set_data.get('set_numero', idx),
                            "juegos_eq1": set_data['puntos_eq1'],
                            "juegos_eq2": set_data['puntos_eq2'],
                            "tiebreak_eq1": set_data.get('tiebreak_eq1'),
                            "tiebreak_eq2": set_data.get('tiebreak_eq2')
                        })
                    # Formato 3: {'set1': {'puntos_eq1': 6, 'puntos_eq2': 4}}
                    elif f'set{idx}' in set_data:
                        set_info = set_data[f'set{idx}']
                        detalle_sets_normalizado.append({
                            "set": idx,
                            "juegos_eq1": set_info.get('puntos_eq1', 0),
                            "juegos_eq2": set_info.get('puntos_eq2', 0),
                            "tiebreak_eq1": set_info.get('tiebreak_eq1'),
                            "tiebreak_eq2": set_info.get('tiebreak_eq2')
                        })
                    # Formato 4: Ya está en formato correcto
                    elif 'juegos_eq1' in set_data and 'juegos_eq2' in set_data:
                        detalle_sets_normalizado.append({
                            "set": set_data.get('set', idx),
                            "juegos_eq1": set_data['juegos_eq1'],
                            "juegos_eq2": set_data['juegos_eq2'],
                            "tiebreak_eq1": set_data.get('tiebreak_eq1'),
                            "tiebreak_eq2": set_data.get('tiebreak_eq2')
                        })
            
            resultado_dict = {
                "id_partido": resultado.id_partido,
                "id_reportador": resultado.id_reportador,
                "sets_eq1": resultado.sets_eq1,
                "sets_eq2": resultado.sets_eq2,
                "detalle_sets": detalle_sets_normalizado,
                "confirmado": resultado.confirmado,
                "desenlace": resultado.desenlace,
                "creado_en": resultado.creado_en
            }
        
        # Obtener historial de rating desde el diccionario
        historial_rating = historial_dict.get(partido.id_partido)
        
        historial_rating_dict = None
        if historial_rating:
            historial_rating_dict = {
                "rating_antes": historial_rating.rating_antes,
                "delta": historial_rating.delta,
                "rating_despues": historial_rating.rating_despues
            }
        
        # Obtener club desde el diccionario
        club = None
        if partido.id_club:
            club_obj = clubs_dict.get(partido.id_club)
            if club_obj:
                club = {
                    "id_club": club_obj.id_club,
                    "nombre": club_obj.nombre,
                    "ciudad": club_obj.ciudad,
                    "pais": club_obj.pais
                }
        
        # Obtener creador desde el diccionario
        creador = usuarios_dict.get(partido.id_creador)
        
        # Obtener categoría si es partido de torneo
        categoria_nombre = None
        if partido.categoria_id:
            categoria_obj = categorias_dict.get(partido.categoria_id)
            if categoria_obj:
                categoria_nombre = categoria_obj.nombre
        
        partidos_completos.append({
            "id_partido": partido.id_partido,
            "fecha": partido.fecha,
            "estado": partido.estado,
            "tipo": partido.tipo if hasattr(partido, 'tipo') else "amistoso",
            "fase": partido.fase if hasattr(partido, 'fase') and partido.fase else None,
            "categoria": categoria_nombre,
            "id_creador": partido.id_creador,
            "creado_en": partido.creado_en,
            "id_club": partido.id_club,
            "jugadores": jugadores_info,
            "resultado": resultado_dict,
            "club": club,
            "creador": {
                "id_usuario": creador.id_usuario,
                "nombre_usuario": creador.nombre_usuario
            } if creador else {},
            "historial_rating": historial_rating_dict
        })
    
    return partidos_completos
