"""
Controller para endpoints de circuitos y ranking por torneo
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case
from typing import List, Optional
from pydantic import BaseModel, Field

from ..database.config import get_db
from ..models.torneo_models import Circuito, Torneo, TorneoCategoria
from ..models.driveplus_models import Usuario, PerfilUsuario, Categoria, HistorialRating, Partido
from ..auth.auth_utils import get_current_user

router = APIRouter(prefix="/circuitos", tags=["Circuitos"])


# ============================================
# SCHEMAS
# ============================================

class CircuitoCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=20)
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    logo_url: Optional[str] = None

class CircuitoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    logo_url: Optional[str] = None
    activo: Optional[bool] = None

class CircuitoResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str]
    logo_url: Optional[str]
    activo: bool
    torneos_count: Optional[int] = 0

class RankingCircuitoItem(BaseModel):
    posicion: int
    id_usuario: int
    nombre_usuario: Optional[str]
    nombre: Optional[str]
    apellido: Optional[str]
    imagen_url: Optional[str]
    categoria: Optional[str]
    puntos: float
    partidos_jugados: int
    partidos_ganados: int
    winrate: float


# ============================================
# ENDPOINTS CRUD CIRCUITOS
# ============================================

@router.get("", response_model=List[CircuitoResponse])
@router.get("/", response_model=List[CircuitoResponse])
async def listar_circuitos(
    activo: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar todos los circuitos"""
    query = db.query(Circuito)
    if activo is not None:
        query = query.filter(Circuito.activo == activo)
    
    circuitos = query.order_by(Circuito.nombre).all()
    
    result = []
    for c in circuitos:
        torneos_count = db.query(func.count(Torneo.id)).filter(Torneo.codigo == c.codigo).scalar() or 0
        result.append(CircuitoResponse(
            id=c.id,
            codigo=c.codigo,
            nombre=c.nombre,
            descripcion=c.descripcion,
            logo_url=c.logo_url,
            activo=c.activo,
            torneos_count=torneos_count
        ))
    
    return result


@router.post("", response_model=CircuitoResponse)
@router.post("/", response_model=CircuitoResponse)
async def crear_circuito(
    data: CircuitoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un circuito (solo administradores)"""
    if not current_user.es_administrador:
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear circuitos")
    
    # Verificar que no exista
    existe = db.query(Circuito).filter(Circuito.codigo == data.codigo.lower()).first()
    if existe:
        raise HTTPException(status_code=400, detail=f"Ya existe un circuito con código '{data.codigo}'")
    
    circuito = Circuito(
        codigo=data.codigo.lower(),
        nombre=data.nombre,
        descripcion=data.descripcion,
        logo_url=data.logo_url,
        creado_por=current_user.id_usuario
    )
    db.add(circuito)
    db.commit()
    db.refresh(circuito)
    
    return CircuitoResponse(
        id=circuito.id,
        codigo=circuito.codigo,
        nombre=circuito.nombre,
        descripcion=circuito.descripcion,
        logo_url=circuito.logo_url,
        activo=circuito.activo,
        torneos_count=0
    )


@router.put("/{circuito_id}", response_model=CircuitoResponse)
async def actualizar_circuito(
    circuito_id: int,
    data: CircuitoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un circuito (solo administradores)"""
    if not current_user.es_administrador:
        raise HTTPException(status_code=403, detail="Solo administradores pueden editar circuitos")
    
    circuito = db.query(Circuito).filter(Circuito.id == circuito_id).first()
    if not circuito:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")
    
    if data.nombre is not None:
        circuito.nombre = data.nombre
    if data.descripcion is not None:
        circuito.descripcion = data.descripcion
    if data.logo_url is not None:
        circuito.logo_url = data.logo_url
    if data.activo is not None:
        circuito.activo = data.activo
    
    db.commit()
    db.refresh(circuito)
    
    torneos_count = db.query(func.count(Torneo.id)).filter(Torneo.codigo == circuito.codigo).scalar() or 0
    
    return CircuitoResponse(
        id=circuito.id,
        codigo=circuito.codigo,
        nombre=circuito.nombre,
        descripcion=circuito.descripcion,
        logo_url=circuito.logo_url,
        activo=circuito.activo,
        torneos_count=torneos_count
    )


@router.delete("/{circuito_id}")
async def eliminar_circuito(
    circuito_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un circuito (solo administradores)"""
    if not current_user.es_administrador:
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar circuitos")
    
    circuito = db.query(Circuito).filter(Circuito.id == circuito_id).first()
    if not circuito:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")
    
    db.delete(circuito)
    db.commit()
    return {"message": f"Circuito '{circuito.nombre}' eliminado"}


# ============================================
# RANKING POR CIRCUITO
# ============================================

@router.get("/{codigo}/ranking", response_model=List[RankingCircuitoItem])
async def ranking_circuito(
    codigo: str,
    categoria: Optional[str] = Query(None, description="Filtrar por categoría (ej: 7ma, 5ta)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Ranking de jugadores en un circuito.
    Suma los deltas positivos de historial_rating para partidos de torneos con ese código.
    Usa la categoría del torneo (partidos.categoria_id -> torneo_categorias) no la actual del usuario.
    Un jugador puede aparecer en múltiples categorías si jugó en distintas.
    """
    codigo = codigo.lower()
    
    # Verificar que el circuito existe
    circuito = db.query(Circuito).filter(Circuito.codigo == codigo).first()
    if not circuito:
        raise HTTPException(status_code=404, detail=f"Circuito '{codigo}' no encontrado")
    
    # Obtener IDs de torneos con este código
    torneo_ids = db.query(Torneo.id).filter(Torneo.codigo == codigo).all()
    torneo_ids = [t[0] for t in torneo_ids]
    
    if not torneo_ids:
        return []
    
    # Subquery: puntos por (usuario, categoria_torneo)
    # Agrupamos por usuario Y por la categoría del partido en el torneo
    puntos_subq = (
        db.query(
            HistorialRating.id_usuario,
            Partido.categoria_id.label("cat_id"),
            func.sum(
                case(
                    (HistorialRating.delta > 0, HistorialRating.delta),
                    else_=0
                )
            ).label("puntos"),
            func.count(func.distinct(HistorialRating.id_partido)).label("partidos_jugados"),
            func.sum(
                case(
                    (HistorialRating.delta > 0, 1),
                    else_=0
                )
            ).label("partidos_ganados")
        )
        .join(Partido, HistorialRating.id_partido == Partido.id_partido)
        .filter(
            Partido.id_torneo.in_(torneo_ids),
            Partido.estado.in_(["finalizado", "confirmado"]),
            Partido.categoria_id.isnot(None)
        )
        .group_by(HistorialRating.id_usuario, Partido.categoria_id)
        .subquery()
    )
    
    # Query principal: join con usuario, perfil, y torneo_categorias para el nombre
    query = (
        db.query(
            puntos_subq.c.id_usuario,
            Usuario.nombre_usuario,
            PerfilUsuario.nombre,
            PerfilUsuario.apellido,
            PerfilUsuario.url_avatar,
            TorneoCategoria.nombre.label("categoria_nombre"),
            puntos_subq.c.puntos,
            puntos_subq.c.partidos_jugados,
            puntos_subq.c.partidos_ganados,
        )
        .join(Usuario, Usuario.id_usuario == puntos_subq.c.id_usuario)
        .join(PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario, isouter=True)
        .join(TorneoCategoria, TorneoCategoria.id == puntos_subq.c.cat_id, isouter=True)
    )
    
    # Filtro por categoría del torneo
    if categoria:
        query = query.filter(TorneoCategoria.nombre == categoria)
    
    # Solo jugadores con puntos > 0
    query = query.filter(puntos_subq.c.puntos > 0)
    
    # Ordenar por puntos descendente
    jugadores = query.order_by(desc(puntos_subq.c.puntos)).limit(limit).all()
    
    result = []
    for i, j in enumerate(jugadores):
        partidos = j.partidos_jugados or 0
        ganados = j.partidos_ganados or 0
        winrate = round((ganados / partidos * 100), 1) if partidos > 0 else 0
        
        result.append(RankingCircuitoItem(
            posicion=i + 1,
            id_usuario=j.id_usuario,
            nombre_usuario=j.nombre_usuario,
            nombre=j.nombre,
            apellido=j.apellido,
            imagen_url=j.url_avatar,
            categoria=j.categoria_nombre,
            puntos=round(float(j.puntos), 1),
            partidos_jugados=partidos,
            partidos_ganados=ganados,
            winrate=winrate
        ))
    
    return result


@router.get("/{codigo}/info")
async def info_circuito(
    codigo: str,
    db: Session = Depends(get_db)
):
    """Obtener info de un circuito con sus torneos"""
    codigo = codigo.lower()
    
    circuito = db.query(Circuito).filter(Circuito.codigo == codigo).first()
    if not circuito:
        raise HTTPException(status_code=404, detail=f"Circuito '{codigo}' no encontrado")
    
    torneos = db.query(
        Torneo.id, Torneo.nombre, Torneo.estado, Torneo.fecha_inicio, Torneo.fecha_fin
    ).filter(Torneo.codigo == codigo).order_by(Torneo.fecha_inicio.desc()).all()
    
    return {
        "id": circuito.id,
        "codigo": circuito.codigo,
        "nombre": circuito.nombre,
        "descripcion": circuito.descripcion,
        "logo_url": circuito.logo_url,
        "activo": circuito.activo,
        "torneos": [
            {
                "id": t.id,
                "nombre": t.nombre,
                "estado": t.estado,
                "fecha_inicio": str(t.fecha_inicio),
                "fecha_fin": str(t.fecha_fin)
            }
            for t in torneos
        ]
    }
