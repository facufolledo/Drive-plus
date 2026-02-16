"""
Controller para endpoints de circuitos y ranking por torneo
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case
from typing import List, Optional
from pydantic import BaseModel, Field

from ..database.config import get_db
from ..models.torneo_models import Circuito, Torneo, TorneoCategoria, CircuitoPuntosJugador, CircuitoPuntosFase
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
    fase_alcanzada: Optional[str] = None
    torneos_jugados: int = 0

class AsignarPuntosRequest(BaseModel):
    torneo_id: int
    categoria_id: int
    usuario_id: int
    fase_alcanzada: str
    puntos: Optional[int] = None  # Si no se pasa, se calcula de la config


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
    Suma los puntos de circuito_puntos_jugador agrupados por usuario y categoría.
    """
    codigo = codigo.lower()
    
    circuito = db.query(Circuito).filter(Circuito.codigo == codigo).first()
    if not circuito:
        raise HTTPException(status_code=404, detail=f"Circuito '{codigo}' no encontrado")
    
    # Subquery: puntos totales por (usuario, categoria)
    puntos_subq = (
        db.query(
            CircuitoPuntosJugador.usuario_id,
            CircuitoPuntosJugador.categoria_id,
            func.sum(CircuitoPuntosJugador.puntos).label("total_puntos"),
            func.count(func.distinct(CircuitoPuntosJugador.torneo_id)).label("torneos_jugados"),
            # Mejor fase alcanzada (la de mayor puntaje)
            func.max(CircuitoPuntosJugador.puntos).label("mejor_puntos"),
        )
        .filter(CircuitoPuntosJugador.circuito_id == circuito.id)
        .group_by(CircuitoPuntosJugador.usuario_id, CircuitoPuntosJugador.categoria_id)
        .subquery()
    )
    
    # Query principal
    query = (
        db.query(
            puntos_subq.c.usuario_id,
            Usuario.nombre_usuario,
            PerfilUsuario.nombre,
            PerfilUsuario.apellido,
            PerfilUsuario.url_avatar,
            TorneoCategoria.nombre.label("categoria_nombre"),
            puntos_subq.c.total_puntos,
            puntos_subq.c.torneos_jugados,
        )
        .join(Usuario, Usuario.id_usuario == puntos_subq.c.usuario_id)
        .join(PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario, isouter=True)
        .join(TorneoCategoria, TorneoCategoria.id == puntos_subq.c.categoria_id, isouter=True)
    )
    
    if categoria:
        query = query.filter(TorneoCategoria.nombre == categoria)
    
    query = query.filter(puntos_subq.c.total_puntos > 0)
    jugadores = query.order_by(desc(puntos_subq.c.total_puntos)).limit(limit).all()
    
    # Para obtener fase_alcanzada del último torneo, hacemos una query extra solo si hay resultados
    # Optimización: obtener la fase del registro con mayor puntos para cada usuario/cat
    fase_map = {}
    if jugadores:
        user_cat_pairs = [(j.usuario_id, j.categoria_nombre) for j in jugadores]
        fases = (
            db.query(
                CircuitoPuntosJugador.usuario_id,
                CircuitoPuntosJugador.categoria_id,
                CircuitoPuntosJugador.fase_alcanzada,
                CircuitoPuntosJugador.puntos,
            )
            .filter(CircuitoPuntosJugador.circuito_id == circuito.id)
            .order_by(CircuitoPuntosJugador.puntos.desc())
            .all()
        )
        for f in fases:
            key = (f.usuario_id, f.categoria_id)
            if key not in fase_map:
                fase_map[key] = f.fase_alcanzada
    
    result = []
    for i, j in enumerate(jugadores):
        # Buscar la fase del registro con cat_id
        cat_id_for_fase = None
        if j.categoria_nombre:
            cat_row = db.query(TorneoCategoria.id).filter(TorneoCategoria.nombre == j.categoria_nombre).first()
            if cat_row:
                cat_id_for_fase = cat_row[0]
        
        fase = fase_map.get((j.usuario_id, cat_id_for_fase)) if cat_id_for_fase else None
        
        result.append(RankingCircuitoItem(
            posicion=i + 1,
            id_usuario=j.usuario_id,
            nombre_usuario=j.nombre_usuario,
            nombre=j.nombre,
            apellido=j.apellido,
            imagen_url=j.url_avatar,
            categoria=j.categoria_nombre,
            puntos=float(j.total_puntos),
            fase_alcanzada=fase,
            torneos_jugados=j.torneos_jugados or 0,
        ))
    
    return result


@router.post("/{codigo}/puntos", status_code=201)
async def asignar_puntos(
    codigo: str,
    data: AsignarPuntosRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Asignar o editar puntos de un jugador en un torneo/categoría (solo admin)"""
    if not current_user.es_administrador:
        raise HTTPException(status_code=403, detail="Solo administradores pueden asignar puntos")
    
    codigo = codigo.lower()
    circuito = db.query(Circuito).filter(Circuito.codigo == codigo).first()
    if not circuito:
        raise HTTPException(status_code=404, detail=f"Circuito '{codigo}' no encontrado")
    
    # Si no se pasan puntos, buscar en la config
    puntos = data.puntos
    if puntos is None:
        config = db.query(CircuitoPuntosFase).filter(
            CircuitoPuntosFase.circuito_id == circuito.id,
            CircuitoPuntosFase.fase == data.fase_alcanzada
        ).first()
        if not config:
            raise HTTPException(status_code=400, detail=f"Fase '{data.fase_alcanzada}' no configurada para este circuito")
        puntos = config.puntos
    
    from sqlalchemy import text
    db.execute(text("""
        INSERT INTO circuito_puntos_jugador (circuito_id, torneo_id, categoria_id, usuario_id, fase_alcanzada, puntos)
        VALUES (:cir, :tor, :cat, :usr, :fase, :pts)
        ON CONFLICT (circuito_id, torneo_id, categoria_id, usuario_id)
        DO UPDATE SET fase_alcanzada = EXCLUDED.fase_alcanzada, puntos = EXCLUDED.puntos
    """), {"cir": circuito.id, "tor": data.torneo_id, "cat": data.categoria_id, "usr": data.usuario_id, "fase": data.fase_alcanzada, "pts": puntos})
    db.commit()
    
    return {"message": f"Puntos asignados: {puntos} pts ({data.fase_alcanzada}) al usuario {data.usuario_id}"}


@router.delete("/{codigo}/puntos")
async def eliminar_puntos(
    codigo: str,
    torneo_id: int = Query(...),
    categoria_id: int = Query(...),
    usuario_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar puntos de un jugador en un torneo/categoría (solo admin)"""
    if not current_user.es_administrador:
        raise HTTPException(status_code=403, detail="Solo administradores")
    
    codigo = codigo.lower()
    circuito = db.query(Circuito).filter(Circuito.codigo == codigo).first()
    if not circuito:
        raise HTTPException(status_code=404, detail=f"Circuito '{codigo}' no encontrado")
    
    deleted = db.query(CircuitoPuntosJugador).filter(
        CircuitoPuntosJugador.circuito_id == circuito.id,
        CircuitoPuntosJugador.torneo_id == torneo_id,
        CircuitoPuntosJugador.categoria_id == categoria_id,
        CircuitoPuntosJugador.usuario_id == usuario_id,
    ).delete()
    db.commit()
    
    return {"message": f"{'Eliminado' if deleted else 'No encontrado'}"}


@router.get("/{codigo}/puntos-config")
async def obtener_config_puntos(
    codigo: str,
    db: Session = Depends(get_db)
):
    """Obtener la configuración de puntos por fase de un circuito"""
    codigo = codigo.lower()
    circuito = db.query(Circuito).filter(Circuito.codigo == codigo).first()
    if not circuito:
        raise HTTPException(status_code=404, detail=f"Circuito '{codigo}' no encontrado")
    
    config = db.query(CircuitoPuntosFase).filter(
        CircuitoPuntosFase.circuito_id == circuito.id
    ).order_by(desc(CircuitoPuntosFase.puntos)).all()
    
    return [{"fase": c.fase, "puntos": c.puntos} for c in config]


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
