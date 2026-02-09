from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta

from ..database.config import get_db
from ..models.driveplus_models import Usuario, PerfilUsuario, Categoria
from ..schemas.ranking import RankingResponse, TopWeeklyResponse
from ..auth.auth_utils import get_current_user
from ..utils.cache import cache, CACHE_TTL

router = APIRouter(prefix="/ranking", tags=["Ranking"])


def _get_ranking_from_db(db: Session, limit: int, offset: int, sexo: Optional[str]) -> List[dict]:
    """Lógica de ranking extraída para poder cachear - OPTIMIZADA"""
    from ..models.driveplus_models import PartidoJugador, ResultadoPartido, Partido, HistorialRating
    from ..models.torneo_models import TorneoPareja
    from sqlalchemy import text
    
    # Subquery para calcular partidos JUGADOS desde historial_rating
    partidos_jugados_subq = (
        db.query(
            HistorialRating.id_usuario,
            func.count(func.distinct(HistorialRating.id_partido)).label("partidos_jugados_real")
        )
        .join(Partido, HistorialRating.id_partido == Partido.id_partido)
        .filter(
            Partido.estado.in_(["finalizado", "confirmado"])
        )
        .group_by(HistorialRating.id_usuario)
        .subquery()
    )
    
    # Subquery para calcular partidos ganados desde historial_rating
    partidos_ganados_subq = (
        db.query(
            HistorialRating.id_usuario,
            func.count(HistorialRating.id_partido).label("partidos_ganados")
        )
        .join(Partido, HistorialRating.id_partido == Partido.id_partido)
        .filter(
            Partido.estado.in_(["finalizado", "confirmado"]),
            HistorialRating.delta > 0  # Delta positivo = victoria
        )
        .group_by(HistorialRating.id_usuario)
        .subquery()
    )
    
    # Subquery para calcular tendencia (últimos 5 partidos)
    # Usamos una window function para obtener los últimos 5 partidos por usuario
    tendencia_subq = (
        db.query(
            HistorialRating.id_usuario,
            func.sum(HistorialRating.delta).label("suma_deltas")
        )
        .join(Partido, HistorialRating.id_partido == Partido.id_partido)
        .filter(Partido.estado.in_(["finalizado", "confirmado"]))
        .group_by(HistorialRating.id_usuario)
        .subquery()
    )
    
    # Query principal con JOIN a las subqueries
    query = (
        db.query(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Usuario.rating,
            func.coalesce(partidos_jugados_subq.c.partidos_jugados_real, 0).label("partidos_jugados"),
            Usuario.sexo,
            PerfilUsuario.nombre,
            PerfilUsuario.apellido,
            PerfilUsuario.ciudad,
            PerfilUsuario.pais,
            PerfilUsuario.url_avatar,
            Categoria.nombre.label("categoria_nombre"),
            func.coalesce(partidos_ganados_subq.c.partidos_ganados, 0).label("partidos_ganados"),
            func.coalesce(tendencia_subq.c.suma_deltas, 0).label("suma_deltas")
        )
        .join(PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario, isouter=True)
        .join(Categoria, Usuario.id_categoria == Categoria.id_categoria, isouter=True)
        .join(partidos_jugados_subq, Usuario.id_usuario == partidos_jugados_subq.c.id_usuario, isouter=True)
        .join(partidos_ganados_subq, Usuario.id_usuario == partidos_ganados_subq.c.id_usuario, isouter=True)
        .join(tendencia_subq, Usuario.id_usuario == tendencia_subq.c.id_usuario, isouter=True)
    )
    
    # Filtrar por sexo si se especifica
    if sexo:
        if sexo in ['M', 'masculino']:
            query = query.filter(Usuario.sexo.in_(['M', 'masculino']))
        elif sexo in ['F', 'femenino']:
            query = query.filter(Usuario.sexo.in_(['F', 'femenino']))
    
    # Ordenar y paginar
    usuarios = query.order_by(desc(Usuario.rating)).offset(offset).limit(limit).all()
    
    # Convertir a dict y calcular tendencia
    result = []
    for u in usuarios:
        suma_deltas = u.suma_deltas or 0
        
        # Calcular tendencia basada en suma de deltas
        if suma_deltas > 10:
            tendencia = "up"
        elif suma_deltas < -10:
            tendencia = "down"
        elif suma_deltas != 0:
            tendencia = "stable"
        else:
            tendencia = "neutral"
        
        result.append({
            "id_usuario": u.id_usuario,
            "nombre_usuario": u.nombre_usuario,
            "rating": u.rating,
            "partidos_jugados": u.partidos_jugados,
            "sexo": u.sexo,
            "nombre": u.nombre,
            "apellido": u.apellido,
            "ciudad": u.ciudad,
            "pais": u.pais,
            "url_avatar": u.url_avatar,
            "categoria_nombre": getattr(u, "categoria_nombre", None),
            "partidos_ganados": u.partidos_ganados,
            "tendencia": tendencia
        })
    
    return result


@router.get("/", response_model=List[RankingResponse])
async def get_ranking(
    limit: int = Query(100, description="Número de jugadores a retornar"),
    offset: int = Query(0, description="Número de jugadores a saltar"),
    sexo: Optional[str] = Query(None, description="Filtrar por sexo: M o F"),
    db: Session = Depends(get_db)
):
    """Obtener el ranking general de jugadores (con caché de 60s)"""
    
    try:
        # Generar cache key
        cache_key = f"ranking:{limit}:{offset}:{sexo or 'all'}"
        
        # Intentar obtener del caché
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            ranking = []
            for i, u in enumerate(cached_data):
                ranking.append(RankingResponse(
                    posicion=offset + i + 1,
                    id_usuario=u["id_usuario"],
                    nombre_usuario=u["nombre_usuario"],
                    nombre=u["nombre"] or "",
                    apellido=u["apellido"] or "",
                    ciudad=u["ciudad"] or "",
                    pais=u["pais"] or "",
                    rating=u["rating"],
                    partidos_jugados=u["partidos_jugados"],
                    partidos_ganados=u["partidos_ganados"],
                    categoria=u["categoria_nombre"],
                    sexo=u["sexo"],
                    imagen_url=u["url_avatar"],
                    tendencia=u.get("tendencia", "neutral")
                ))
            return ranking
        
        # Cache miss - obtener de DB (ya incluye tendencia calculada)
        usuarios_data = _get_ranking_from_db(db, limit, offset, sexo)
        
        # Guardar en caché
        cache.set(cache_key, usuarios_data, CACHE_TTL["ranking"])
        
        # Formatear respuesta
        ranking = []
        for i, u in enumerate(usuarios_data):
            ranking.append(RankingResponse(
                posicion=offset + i + 1,
                id_usuario=u["id_usuario"],
                nombre_usuario=u["nombre_usuario"],
                nombre=u["nombre"] or "",
                apellido=u["apellido"] or "",
                ciudad=u["ciudad"] or "",
                pais=u["pais"] or "",
                rating=u["rating"],
                partidos_jugados=u["partidos_jugados"],
                partidos_ganados=u["partidos_ganados"],
                categoria=u["categoria_nombre"],
                sexo=u["sexo"],
                imagen_url=u["url_avatar"],
                tendencia=u.get("tendencia", "neutral")
            ))
        
        return ranking
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el ranking: {str(e)}"
        )


@router.get("/top-weekly", response_model=List[TopWeeklyResponse])
async def get_top_weekly(
    limit: int = Query(5, description="Número de jugadores a retornar"),
    db: Session = Depends(get_db)
):
    """Obtener los mejores jugadores de la semana (con caché de 2 min)"""
    
    try:
        cache_key = f"top_weekly:{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Obtener usuarios con mejor rating
        usuarios = db.query(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Usuario.rating,
            PerfilUsuario.nombre,
            PerfilUsuario.apellido,
            PerfilUsuario.ciudad,
            PerfilUsuario.url_avatar
        ).join(
            PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario, isouter=True
        ).order_by(
            desc(Usuario.rating)
        ).limit(limit).all()
        
        top_weekly = []
        for u in usuarios:
            nombre_completo = f"{u.nombre or ''} {u.apellido or ''}".strip() or u.nombre_usuario
            top_weekly.append(TopWeeklyResponse(
                id=u.id_usuario,
                nombre=nombre_completo,
                ciudad=u.ciudad or "",
                puntos=u.rating,
                imagen_url=u.url_avatar,
                rating=u.rating
            ))
        
        # Cachear por 2 minutos
        cache.set(cache_key, top_weekly, 120)
        
        return top_weekly
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el ranking semanal: {str(e)}"
        )


@router.get("/historial/{user_id}")
async def get_historial_elo(
    user_id: int,
    limit: int = Query(20, description="Número de registros a retornar"),
    db: Session = Depends(get_db)
):
    """Obtener el historial de cambios de rating de un usuario"""
    
    try:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # TODO: Implementar con tabla real de historial
        historial = [
            {
                "fecha": "2024-09-01",
                "rating_anterior": 1427,
                "rating_nuevo": 1450,
                "cambio": 23,
                "partido_id": 1
            }
        ]
        
        return {
            "usuario_id": user_id,
            "historial": historial[:limit]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el historial: {str(e)}"
        )
