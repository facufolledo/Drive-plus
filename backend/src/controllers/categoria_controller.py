from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from typing import List

from ..database.config import get_db
from ..models.driveplus_models import Categoria, Usuario
from ..schemas.categoria import CategoriaResponse, JugadoresPorCategoriaResponse, JugadorCategoriaResponse

router = APIRouter(prefix="/categorias", tags=["Categorías"])

@router.get("", response_model=List[CategoriaResponse])
@router.get("/", response_model=List[CategoriaResponse])
async def get_categorias(sexo: str = None, db: Session = Depends(get_db)):
    """Obtener todas las categorías, opcionalmente filtradas por sexo"""
    query = db.query(Categoria)
    if sexo:
        query = query.filter(Categoria.sexo == sexo)
    categorias = query.order_by(Categoria.sexo, Categoria.rating_min.asc()).all()
    return categorias

@router.get("/{categoria_id}", response_model=CategoriaResponse)
async def get_categoria(categoria_id: int, db: Session = Depends(get_db)):
    """Obtener una categoría específica"""
    categoria = db.query(Categoria).filter(Categoria.id_categoria == categoria_id).first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    return categoria

   

@router.get("/usuario/{usuario_id}/categoria", response_model=CategoriaResponse)
async def get_categoria_por_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtener la categoría de un jugador específico por su ID"""
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Buscar la categoría que contenga el rating y sea del mismo sexo
    categoria = db.query(Categoria).filter(
        Categoria.sexo == usuario.sexo &
        (Categoria.rating_min.is_(None) | (Categoria.rating_min <= usuario.rating)) &
        (Categoria.rating_max.is_(None) | (Categoria.rating_max >= usuario.rating))
    ).order_by(Categoria.rating_min.desc()).first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se pudo determinar la categoría del usuario"
        )
    
    return categoria

@router.get("/ranking/global", response_model=List[dict])
async def get_ranking_global(db: Session = Depends(get_db), limit: int = 100):
    """Obtener ranking global de jugadores"""
    jugadores = db.query(
        Usuario.id_usuario,
        Usuario.nombre_usuario,
        Usuario.rating,
        Usuario.partidos_jugados
    ).order_by(Usuario.rating.desc()).limit(limit).all()
    
    ranking = []
    for i, jugador in enumerate(jugadores, 1):
        ranking.append({
            "posicion": i,
            "id_usuario": jugador.id_usuario,
            "nombre_usuario": jugador.nombre_usuario,
            "rating": jugador.rating,
            "partidos_jugados": jugador.partidos_jugados
        })
    
    return ranking

@router.get("/{categoria_id}/jugadores", response_model=JugadoresPorCategoriaResponse)
async def get_jugadores_por_categoria(
    categoria_id: int, 
    sexo: str = "masculino",
    db: Session = Depends(get_db)
):
    """Obtener todos los jugadores de una categoría específica filtrados por sexo"""
    from ..models.driveplus_models import PerfilUsuario, Partido, HistorialRating
    from sqlalchemy import func, desc
    
    # Convertir sexo a letra para usuarios (M/F)
    sexo_usuario = 'M' if sexo == 'masculino' else 'F'
    
    # Buscar categoría por ID y sexo
    categoria = db.query(Categoria).filter(
        Categoria.id_categoria == categoria_id,
        Categoria.sexo == sexo
    ).first()
    
    # Si no se encuentra por ID, intentar buscar por nombre de categoría común
    if not categoria:
        # Mapeo de IDs del frontend a nombres de categoría
        categoria_nombres = {
            7: "Principiante",
            1: "8va",
            2: "7ma", 
            3: "6ta",
            4: "5ta",
            5: "4ta",
            6: "Libre"
        }
        
        nombre_categoria = categoria_nombres.get(categoria_id)
        if nombre_categoria:
            categoria = db.query(Categoria).filter(
                Categoria.nombre == nombre_categoria,
                Categoria.sexo == sexo
            ).first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría no encontrada para sexo {sexo}"
        )
    
    # Subqueries para partidos jugados y ganados
    partidos_jugados_subq = (
        db.query(
            HistorialRating.id_usuario,
            func.count(func.distinct(HistorialRating.id_partido)).label("partidos_jugados_real")
        )
        .join(Partido, HistorialRating.id_partido == Partido.id_partido)
        .filter(Partido.estado.in_(["finalizado", "confirmado"]))
        .group_by(HistorialRating.id_usuario)
        .subquery()
    )
    
    partidos_ganados_subq = (
        db.query(
            HistorialRating.id_usuario,
            func.count(HistorialRating.id_partido).label("partidos_ganados")
        )
        .join(Partido, HistorialRating.id_partido == Partido.id_partido)
        .filter(
            Partido.estado.in_(["finalizado", "confirmado"]),
            HistorialRating.delta > 0
        )
        .group_by(HistorialRating.id_usuario)
        .subquery()
    )
    
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
    
    # Query base con JOINs a subqueries y perfil
    query = (
        db.query(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Usuario.rating,
            Usuario.sexo,
            func.coalesce(partidos_jugados_subq.c.partidos_jugados_real, 0).label("partidos_jugados"),
            func.coalesce(partidos_ganados_subq.c.partidos_ganados, 0).label("partidos_ganados"),
            func.coalesce(tendencia_subq.c.suma_deltas, 0).label("suma_deltas"),
            PerfilUsuario.nombre,
            PerfilUsuario.apellido,
            PerfilUsuario.url_avatar,
        )
        .join(PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario, isouter=True)
        .join(partidos_jugados_subq, Usuario.id_usuario == partidos_jugados_subq.c.id_usuario, isouter=True)
        .join(partidos_ganados_subq, Usuario.id_usuario == partidos_ganados_subq.c.id_usuario, isouter=True)
        .join(tendencia_subq, Usuario.id_usuario == tendencia_subq.c.id_usuario, isouter=True)
        .filter(Usuario.sexo == sexo_usuario)
    )
    
    # Filtrar por rango de rating de la categoría
    if categoria.rating_min is not None and categoria.rating_max is not None:
        query = query.filter(
            Usuario.rating >= categoria.rating_min,
            Usuario.rating <= categoria.rating_max
        )
    elif categoria.rating_min is not None:
        query = query.filter(Usuario.rating >= categoria.rating_min)
    elif categoria.rating_max is not None:
        query = query.filter(Usuario.rating <= categoria.rating_max)
    else:
        query = query.filter(Usuario.id_categoria == categoria_id)
    
    jugadores = query.order_by(desc(Usuario.rating)).all()
    
    # Convertir a la respuesta esperada
    jugadores_response = []
    for j in jugadores:
        suma_deltas = j.suma_deltas or 0
        if suma_deltas > 10:
            tendencia = "up"
        elif suma_deltas < -10:
            tendencia = "down"
        elif suma_deltas != 0:
            tendencia = "stable"
        else:
            tendencia = "neutral"
        
        jugadores_response.append(JugadorCategoriaResponse(
            id_usuario=j.id_usuario,
            nombre_usuario=j.nombre_usuario,
            nombre=j.nombre or "",
            apellido=j.apellido or "",
            rating=j.rating,
            partidos_jugados=j.partidos_jugados,
            partidos_ganados=j.partidos_ganados,
            sexo=j.sexo,
            imagen_url=j.url_avatar,
            tendencia=tendencia
        ))
    
    return JugadoresPorCategoriaResponse(
        categoria=categoria,
        jugadores=jugadores_response,
        total_jugadores=len(jugadores_response)
    )
