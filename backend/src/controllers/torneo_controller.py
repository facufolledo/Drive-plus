"""
Controller para endpoints de torneos
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database.config import get_db
from ..services.torneo_service import TorneoService
from ..services.torneo_inscripcion_service import TorneoInscripcionService
from ..schemas.torneo_schemas import (
    TorneoCreate, TorneoUpdate, TorneoResponse,
    EstadisticasTorneoResponse,
    ParejaInscripcion, ParejaUpdate, ParejaResponse
)
from ..auth.auth_utils import get_current_user, get_current_user_optional
from ..models.driveplus_models import Usuario

router = APIRouter(prefix="/torneos", tags=["Torneos"])


# ============================================
# MODELOS AUXILIARES
# ============================================

class BajaParejaRequest(BaseModel):
    motivo: Optional[str] = None


# ============================================
# ENDPOINTS ESPECÍFICOS (DEBEN IR ANTES QUE LOS DINÁMICOS)
# ============================================

@router.get("/mis-invitaciones-simple")
def mis_invitaciones_simple():
    """Endpoint ultra simple sin dependencias para test"""
    return {"mensaje": "Endpoint funcionando", "invitaciones": []}


@router.get("/test-auth")
async def test_auth(current_user: Usuario = Depends(get_current_user)):
    """Test simple de autenticación"""
    return {
        "authenticated": True,
        "user_id": current_user.id_usuario,
        "user_name": getattr(current_user, 'nombre_usuario', 'N/A')
    }


@router.get("/debug/mis-invitaciones")
async def debug_mis_invitaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint de debug para mis-invitaciones
    """
    try:
        from ..models.torneo_models import TorneoPareja
        
        # Info del usuario actual
        user_info = {
            "user_id": current_user.id_usuario,
            "user_name": getattr(current_user, 'nombre_usuario', 'N/A')
        }
        
        # Contar todas las parejas del usuario
        total_parejas = db.query(TorneoPareja).filter(
            (TorneoPareja.jugador1_id == current_user.id_usuario) |
            (TorneoPareja.jugador2_id == current_user.id_usuario)
        ).count()
        
        # Parejas como jugador2
        parejas_jugador2 = db.query(TorneoPareja).filter(
            TorneoPareja.jugador2_id == current_user.id_usuario
        ).all()
        
        # Estados únicos
        from sqlalchemy import distinct
        estados_unicos = db.query(distinct(TorneoPareja.estado)).all()
        
        # Parejas pendientes
        parejas_pendientes = db.query(TorneoPareja).filter(
            TorneoPareja.jugador2_id == current_user.id_usuario,
            TorneoPareja.estado == 'pendiente'
        ).all()
        
        # Parejas no confirmadas
        parejas_no_confirmadas = db.query(TorneoPareja).filter(
            TorneoPareja.jugador2_id == current_user.id_usuario,
            TorneoPareja.estado == 'pendiente',
            TorneoPareja.confirmado_jugador2 == False
        ).all()
        
        return {
            "user_info": user_info,
            "total_parejas": total_parejas,
            "parejas_como_jugador2": len(parejas_jugador2),
            "estados_en_db": [e[0] for e in estados_unicos],
            "parejas_pendientes": len(parejas_pendientes),
            "parejas_no_confirmadas": len(parejas_no_confirmadas),
            "detalle_parejas_jugador2": [
                {
                    "id": p.id,
                    "torneo_id": p.torneo_id,
                    "estado": p.estado,
                    "confirmado_j1": p.confirmado_jugador1,
                    "confirmado_j2": p.confirmado_jugador2
                }
                for p in parejas_jugador2
            ]
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/mis-invitaciones")
@router.get("/mis-invitaciones/")
async def obtener_mis_invitaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene las invitaciones pendientes del usuario actual
    """
    try:
        from ..models.torneo_models import TorneoPareja, Torneo
        from ..models.driveplus_models import PerfilUsuario
        
        # Buscar parejas donde el usuario es jugador2 y está pendiente de confirmación
        parejas = db.query(TorneoPareja).filter(
            TorneoPareja.jugador2_id == current_user.id_usuario,
            TorneoPareja.estado == 'pendiente',
            TorneoPareja.confirmado_jugador2 == False
        ).all()
        
        # Simplificar la respuesta para evitar problemas de serialización
        resultado = []
        for pareja in parejas:
            try:
                # Obtener info básica sin joins complejos
                item = {
                    'pareja_id': pareja.id,
                    'torneo_id': pareja.torneo_id,
                    'companero_id': pareja.jugador1_id,
                    'codigo': pareja.codigo_confirmacion or "",  # Cambiado de codigo_confirmacion a codigo
                    'fecha_expiracion': None
                }
                
                # Intentar obtener nombres solo si es posible
                try:
                    torneo = db.query(Torneo).filter(Torneo.id == pareja.torneo_id).first()
                    if torneo:
                        item['torneo_nombre'] = torneo.nombre
                    else:
                        item['torneo_nombre'] = 'Torneo'
                        
                    perfil = db.query(PerfilUsuario).filter(
                        PerfilUsuario.id_usuario == pareja.jugador1_id
                    ).first()
                    if perfil:
                        item['companero_nombre'] = f"{perfil.nombre} {perfil.apellido}"
                    else:
                        item['companero_nombre'] = f'Jugador {pareja.jugador1_id}'
                        
                    if pareja.fecha_expiracion:
                        item['fecha_expiracion'] = pareja.fecha_expiracion.isoformat()
                        
                except Exception:
                    # Si falla obtener nombres, usar valores por defecto
                    item['torneo_nombre'] = 'Torneo'
                    item['companero_nombre'] = f'Jugador {pareja.jugador1_id}'
                
                resultado.append(item)
                
            except Exception as inner_e:
                # Si hay error con una pareja específica, continuar
                continue
        
        return {"invitaciones": resultado}
        
    except Exception as e:
        # Devolver error 500 en lugar de 422
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


# ============================================
# ENDPOINTS DINÁMICOS (DEBEN IR DESPUÉS DE LOS ESPECÍFICOS)
# ============================================

@router.post("", response_model=TorneoResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=TorneoResponse, status_code=status.HTTP_201_CREATED)
async def crear_torneo(
    torneo_data: TorneoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo torneo
    
    Solo usuarios autorizados pueden crear torneos
    """
    try:
        user_id = current_user.id_usuario
        torneo = TorneoService.crear_torneo(db, torneo_data, user_id)
        return torneo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/test-simple")
def test_simple():
    """Endpoint de prueba ultra simple"""
    return {"status": "ok", "message": "Torneo controller funcionando"}


@router.get("/lista")
def listar_torneos_alternativo():
    """Endpoint alternativo para listar torneos"""
    return {"torneos": [], "total": 0, "message": "Lista de torneos (alternativo)"}


@router.get("")
@router.get("/")
def listar_torneos(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    categoria: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista todos los torneos con filtros opcionales
    
    - **skip**: Número de registros a saltar (paginación)
    - **limit**: Número máximo de registros a devolver
    - **estado**: Filtrar por estado (inscripcion, fase_grupos, etc.)
    - **categoria**: Filtrar por categoría
    """
    try:
        # Simplificar temporalmente para debug
        from ..models.torneo_models import Torneo
        
        query = db.query(Torneo)
        
        if estado:
            query = query.filter(Torneo.estado == estado)
        
        if categoria:
            query = query.filter(Torneo.categoria == categoria)
        
        # Usar created_at en lugar de fecha_inicio para el ordenamiento
        torneos = query.order_by(Torneo.created_at.desc()).offset(skip).limit(limit).all()
        
        # Conteo de parejas en una sola query (evitar N+1)
        from ..models.torneo_models import TorneoPareja
        from sqlalchemy import func
        torneo_ids = [t.id for t in torneos]
        parejas_por_torneo = {}
        if torneo_ids:
            counts = db.query(TorneoPareja.torneo_id, func.count(TorneoPareja.id)).filter(
                TorneoPareja.torneo_id.in_(torneo_ids),
                TorneoPareja.estado.in_(['inscripta', 'confirmada'])
            ).group_by(TorneoPareja.torneo_id).all()
            parejas_por_torneo = {tid: c for tid, c in counts}
        
        resultado = []
        for torneo in torneos:
            parejas_count = parejas_por_torneo.get(torneo.id, 0)
            resultado.append({
                "id": torneo.id,
                "nombre": torneo.nombre,
                "descripcion": torneo.descripcion,
                "tipo": torneo.tipo,
                "categoria": torneo.categoria,
                "genero": torneo.genero or 'masculino',
                "estado": torneo.estado,
                "fecha_inicio": torneo.fecha_inicio.isoformat() if torneo.fecha_inicio else None,
                "fecha_fin": torneo.fecha_fin.isoformat() if torneo.fecha_fin else None,
                "lugar": torneo.lugar,
                "created_at": torneo.created_at.isoformat() if torneo.created_at else None,
                "parejas_inscritas": parejas_count,
                # Campos de pago
                "requiere_pago": torneo.requiere_pago or False,
                "monto_inscripcion": float(torneo.monto_inscripcion) if torneo.monto_inscripcion else 0,
                "alias_cbu_cvu": torneo.alias_cbu_cvu,
                "titular_cuenta": torneo.titular_cuenta,
                "banco": torneo.banco,
                "telefono_contacto": torneo.telefono_contacto,
                # Horarios
                "horarios_disponibles": torneo.horarios_disponibles,
            })
        
        return resultado
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al listar torneos: {str(e)}"
        )


@router.get("/mis-torneos")
@router.get("/mis-torneos/")
async def obtener_mis_torneos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene los torneos donde el usuario está inscripto (como jugador1 o jugador2)
    """
    from ..models.torneo_models import TorneoPareja, Torneo
    from sqlalchemy import or_
    
    try:
        # Buscar parejas donde el usuario participa
        parejas = db.query(TorneoPareja).filter(
            or_(
                TorneoPareja.jugador1_id == current_user.id_usuario,
                TorneoPareja.jugador2_id == current_user.id_usuario
            ),
            TorneoPareja.estado.in_(['inscripta', 'confirmada'])  # Removido 'pendiente' que no existe en el enum
        ).all()
        
        if not parejas:
            return {"torneos": []}
        
        # Obtener IDs únicos de torneos
        torneo_ids = list(set(p.torneo_id for p in parejas))
        
        # Obtener info de los torneos
        torneos = db.query(Torneo).filter(Torneo.id.in_(torneo_ids)).all()
        
        # Crear dict de parejas por torneo para incluir estado de inscripción
        parejas_por_torneo = {}
        for p in parejas:
            parejas_por_torneo[p.torneo_id] = {
                "pareja_id": p.id,
                "estado_inscripcion": p.estado.value if hasattr(p.estado, 'value') else str(p.estado),
                "categoria_id": p.categoria_id
            }
        
        resultado = []
        for torneo in torneos:
            info_pareja = parejas_por_torneo.get(torneo.id, {})
            resultado.append({
                "id": torneo.id,
                "nombre": torneo.nombre,
                "descripcion": torneo.descripcion,
                "tipo": torneo.tipo.value if hasattr(torneo.tipo, 'value') else str(torneo.tipo),
                "categoria": torneo.categoria,
                "genero": torneo.genero or 'masculino',
                "estado": torneo.estado.value if hasattr(torneo.estado, 'value') else str(torneo.estado),
                "fecha_inicio": torneo.fecha_inicio.isoformat() if torneo.fecha_inicio else None,
                "fecha_fin": torneo.fecha_fin.isoformat() if torneo.fecha_fin else None,
                "lugar": torneo.lugar,
                "mi_inscripcion": info_pareja
            })
        
        return {"torneos": resultado}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{torneo_id}")
async def obtener_torneo(
    torneo_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """Obtiene un torneo por ID"""
    from ..models.torneo_models import TorneoPareja
    from ..services.torneo_zona_service import TorneoZonaService
    
    torneo = TorneoService.obtener_torneo(db, torneo_id)
    if not torneo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Torneo no encontrado")
    
    # Contar parejas inscritas
    parejas_count = db.query(TorneoPareja).filter(
        TorneoPareja.torneo_id == torneo.id,
        TorneoPareja.estado.in_(['inscripta', 'confirmada'])
    ).count()
    
    # Verificar si el usuario actual es organizador
    es_organizador = False
    if current_user:
        es_organizador = TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario)
    
    return {
        "id": torneo.id,
        "nombre": torneo.nombre,
        "descripcion": torneo.descripcion,
        "tipo": torneo.tipo.value if hasattr(torneo.tipo, 'value') else str(torneo.tipo),
        "categoria": torneo.categoria,
        "genero": torneo.genero or 'masculino',
        "estado": torneo.estado.value if hasattr(torneo.estado, 'value') else str(torneo.estado),
        "fecha_inicio": torneo.fecha_inicio.isoformat() if torneo.fecha_inicio else None,
        "fecha_fin": torneo.fecha_fin.isoformat() if torneo.fecha_fin else None,
        "lugar": torneo.lugar,
        "reglas_json": torneo.reglas_json,
        "horarios_disponibles": torneo.horarios_disponibles,
        "creado_por": torneo.creado_por,
        "created_at": torneo.created_at.isoformat() if torneo.created_at else None,
        "updated_at": torneo.updated_at.isoformat() if torneo.updated_at else None,
        "parejas_inscritas": parejas_count,
        "total_partidos": 0,
        "es_organizador": es_organizador,
        # Campos de pago
        "requiere_pago": torneo.requiere_pago or False,
        "monto_inscripcion": float(torneo.monto_inscripcion) if torneo.monto_inscripcion else 0,
        "alias_cbu_cvu": torneo.alias_cbu_cvu,
        "titular_cuenta": torneo.titular_cuenta,
        "banco": torneo.banco,
        "telefono_contacto": torneo.telefono_contacto,
    }


@router.put("/{torneo_id}", response_model=TorneoResponse)
def actualizar_torneo(
    torneo_id: int,
    torneo_data: TorneoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un torneo
    
    Solo organizadores del torneo pueden actualizarlo
    """
    try:
        user_id = current_user.id_usuario
        torneo = TorneoService.actualizar_torneo(db, torneo_id, torneo_data, user_id)
        return torneo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{torneo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_torneo(
    torneo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina un torneo
    
    Solo el owner puede eliminar el torneo
    Solo se puede eliminar si está en estado de inscripción
    """
    try:
        user_id = current_user.id_usuario
        TorneoService.eliminar_torneo(db, torneo_id, user_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{torneo_id}/organizadores")
def agregar_organizador(
    torneo_id: int,
    nuevo_organizador_id: int,
    rol: str = "colaborador",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Agrega un organizador al torneo
    
    Solo el owner puede agregar organizadores
    """
    try:
        user_id = current_user.id_usuario
        organizador = TorneoService.agregar_organizador(
            db, torneo_id, nuevo_organizador_id, user_id, rol
        )
        return {"message": "Organizador agregado exitosamente", "organizador_id": organizador.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{torneo_id}/organizadores/{organizador_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_organizador(
    torneo_id: int,
    organizador_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Remueve un organizador del torneo
    
    Solo el owner puede remover organizadores
    No se puede remover al owner
    """
    try:
        user_id = current_user.id_usuario
        TorneoService.remover_organizador(db, torneo_id, organizador_id, user_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{torneo_id}/organizadores")
def listar_organizadores(
    torneo_id: int,
    db: Session = Depends(get_db)
):
    """Lista todos los organizadores de un torneo"""
    try:
        organizadores = TorneoService.listar_organizadores(db, torneo_id)
        return organizadores
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{torneo_id}/estado")
def cambiar_estado(
    torneo_id: int,
    nuevo_estado: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cambia el estado de un torneo
    
    Transiciones válidas:
    - inscripcion -> armando_zonas
    - armando_zonas -> fase_grupos
    - fase_grupos -> fase_eliminacion
    - fase_eliminacion -> finalizado
    """
    try:
        user_id = current_user.id_usuario
        torneo = TorneoService.cambiar_estado(db, torneo_id, nuevo_estado, user_id)
        return torneo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{torneo_id}/estadisticas", response_model=EstadisticasTorneoResponse)
def obtener_estadisticas(
    torneo_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas generales del torneo"""
    from ..models.torneo_models import TorneoPareja, TorneoZona
    from ..models.driveplus_models import Partido
    
    torneo = TorneoService.obtener_torneo(db, torneo_id)
    if not torneo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Torneo no encontrado")
    
    # Contar parejas
    total_parejas = db.query(TorneoPareja).filter(
        TorneoPareja.torneo_id == torneo_id,
        TorneoPareja.estado == "confirmada"
    ).count()
    
    # Contar partidos
    total_partidos = db.query(Partido).filter(
        Partido.id_torneo == torneo_id
    ).count()
    
    partidos_jugados = db.query(Partido).filter(
        Partido.id_torneo == torneo_id,
        Partido.estado == "finalizado"
    ).count()
    
    partidos_pendientes = total_partidos - partidos_jugados
    
    # Contar zonas
    zonas = db.query(TorneoZona).filter(
        TorneoZona.torneo_id == torneo_id
    ).count()
    
    return EstadisticasTorneoResponse(
        torneo_id=torneo_id,
        total_parejas=total_parejas,
        total_partidos=total_partidos,
        partidos_jugados=partidos_jugados,
        partidos_pendientes=partidos_pendientes,
        zonas=zonas,
        fase_actual=torneo.estado
    )


# ============================================
# ENDPOINTS DE CATEGORÍAS
# ============================================

class CategoriaCreateBody(BaseModel):
    nombre: str
    genero: str = "masculino"
    max_parejas: int = 16
    orden: int = 0


@router.post("/{torneo_id}/categorias", status_code=status.HTTP_201_CREATED)
def crear_categoria(
    torneo_id: int,
    categoria_data: CategoriaCreateBody,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva categoría en el torneo (8va, 6ta, 4ta, Libre, etc.)"""
    from ..models.torneo_models import TorneoCategoria
    from ..services.torneo_zona_service import TorneoZonaService
    
    try:
        if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        categoria = TorneoCategoria(
            torneo_id=torneo_id,
            nombre=categoria_data.nombre,
            genero=categoria_data.genero,
            max_parejas=categoria_data.max_parejas,
            orden=categoria_data.orden
        )
        db.add(categoria)
        db.commit()
        db.refresh(categoria)
        
        return {
            "id": categoria.id,
            "torneo_id": categoria.torneo_id,
            "nombre": categoria.nombre,
            "genero": categoria.genero,
            "max_parejas": categoria.max_parejas,
            "estado": categoria.estado,
            "orden": categoria.orden,
            "parejas_inscritas": 0
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{torneo_id}/categorias")
@router.get("/{torneo_id}/categorias/")
def listar_categorias(
    torneo_id: int,
    db: Session = Depends(get_db)
):
    """Lista todas las categorías del torneo con conteo de parejas"""
    try:
        from ..models.torneo_models import TorneoCategoria, TorneoPareja
        
        categorias = db.query(TorneoCategoria).filter(
            TorneoCategoria.torneo_id == torneo_id
        ).order_by(TorneoCategoria.orden).all()
        
        # Conteo de parejas por categoría en una sola query (evitar N+1)
        from sqlalchemy import func
        cat_ids = [c.id for c in categorias]
        parejas_por_cat = {}
        if cat_ids:
            counts = db.query(TorneoPareja.categoria_id, func.count(TorneoPareja.id)).filter(
                TorneoPareja.categoria_id.in_(cat_ids),
                TorneoPareja.estado.in_(['inscripta', 'confirmada'])
            ).group_by(TorneoPareja.categoria_id).all()
            parejas_por_cat = {cid: c for cid, c in counts}
        
        resultado = []
        for cat in categorias:
            parejas_count = parejas_por_cat.get(cat.id, 0)
            resultado.append({
                "id": cat.id,
                "torneo_id": cat.torneo_id,
                "nombre": cat.nombre,
                "genero": cat.genero,
                "max_parejas": cat.max_parejas,
                "estado": cat.estado,
                "orden": cat.orden,
                "parejas_inscritas": parejas_count
            })
        
        return resultado
        
    except Exception as e:
        # Si hay error, devolver lista vacía en lugar de fallar
        print(f"Error en listar_categorias: {e}")
        return []


@router.put("/{torneo_id}/categorias/{categoria_id}")
def actualizar_categoria(
    torneo_id: int,
    categoria_id: int,
    categoria_data: CategoriaCreateBody,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una categoría del torneo"""
    from ..models.torneo_models import TorneoCategoria
    from ..services.torneo_zona_service import TorneoZonaService
    
    if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    categoria = db.query(TorneoCategoria).filter(
        TorneoCategoria.id == categoria_id,
        TorneoCategoria.torneo_id == torneo_id
    ).first()
    
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    categoria.nombre = categoria_data.nombre
    categoria.genero = categoria_data.genero
    categoria.max_parejas = categoria_data.max_parejas
    categoria.orden = categoria_data.orden
    db.commit()
    
    return {"message": "Categoría actualizada", "id": categoria.id}


@router.delete("/{torneo_id}/categorias/{categoria_id}")
def eliminar_categoria(
    torneo_id: int,
    categoria_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina una categoría (solo si no tiene parejas inscritas)"""
    from ..models.torneo_models import TorneoCategoria, TorneoPareja
    from ..services.torneo_zona_service import TorneoZonaService
    
    if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    # Verificar que no tenga parejas
    parejas_count = db.query(TorneoPareja).filter(
        TorneoPareja.categoria_id == categoria_id
    ).count()
    
    if parejas_count > 0:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar: hay {parejas_count} parejas inscritas")
    
    db.query(TorneoCategoria).filter(
        TorneoCategoria.id == categoria_id,
        TorneoCategoria.torneo_id == torneo_id
    ).delete()
    db.commit()
    
    return {"message": "Categoría eliminada"}


# ============================================
# ENDPOINTS DE INSCRIPCIONES
# ============================================

@router.post("/{torneo_id}/inscribir", status_code=status.HTTP_201_CREATED)
async def inscribir_pareja(
    torneo_id: int,
    request_body: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Inscribe una pareja en el torneo
    
    - Si es ORGANIZADOR: Inscripción directa y confirmada
    - Si es JUGADOR: Requiere confirmación del compañero
    """
    from ..services.torneo_confirmacion_service import TorneoConfirmacionService
    from ..services.torneo_zona_service import TorneoZonaService
    from ..models.torneo_models import TorneoPareja
    
    # Validar con Pydantic
    try:
        pareja_data = ParejaInscripcion(**request_body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Obtener disponibilidad del request original (Pydantic puede excluirla)
    disponibilidad = request_body.get('disponibilidad_horaria')
    
    try:
        user_id = current_user.id_usuario
        
        # Verificar si el usuario es organizador del torneo
        es_organizador = TorneoZonaService._es_organizador(db, torneo_id, user_id)
        
        if es_organizador:
            # ORGANIZADOR: Inscripción directa y confirmada
            pareja = TorneoPareja(
                torneo_id=torneo_id,
                categoria_id=pareja_data.categoria_id,
                jugador1_id=pareja_data.jugador1_id,
                jugador2_id=pareja_data.jugador2_id,
                estado='confirmada',
                confirmado_jugador1=True,
                confirmado_jugador2=True,
                creado_por_id=user_id,
                observaciones=pareja_data.observaciones,
                disponibilidad_horaria=disponibilidad
            )
            db.add(pareja)
            db.commit()
            db.refresh(pareja)
            
            return {
                "mensaje": "Pareja inscrita y confirmada automáticamente (organizador)",
                "pareja_id": pareja.id,
                "estado": "confirmada",
                "es_organizador": True
            }
        else:
            # JUGADOR: Proceso normal con confirmación
            resultado = TorneoConfirmacionService.crear_inscripcion_pendiente(
                db=db,
                torneo_id=torneo_id,
                jugador1_id=pareja_data.jugador1_id,
                jugador2_id=pareja_data.jugador2_id,
                categoria_id=pareja_data.categoria_id,
                creador_id=user_id,
                observaciones=pareja_data.observaciones,
                disponibilidad_horaria=disponibilidad
            )
            
            # Obtener info del torneo para datos de pago
            from ..models.torneo_models import Torneo
            torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
            
            if torneo and torneo.requiere_pago:
                resultado['requiere_pago'] = True
                resultado['monto_inscripcion'] = float(torneo.monto_inscripcion) if torneo.monto_inscripcion else 0
                resultado['alias_cbu_cvu'] = torneo.alias_cbu_cvu
                resultado['titular_cuenta'] = torneo.titular_cuenta
                resultado['banco'] = torneo.banco
            else:
                resultado['requiere_pago'] = False
            
            return resultado
            
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{torneo_id}/parejas/{pareja_id}/restricciones")
async def actualizar_restricciones_pareja(
    torneo_id: int,
    pareja_id: int,
    restricciones: dict,  # {"disponibilidad_horaria": [{dias: [], horaInicio: "", horaFin: ""}]}
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Permite a los jugadores de una pareja actualizar sus restricciones horarias
    """
    from ..models.torneo_models import TorneoPareja
    
    try:
        # Buscar la pareja
        pareja = db.query(TorneoPareja).filter(
            TorneoPareja.id == pareja_id,
            TorneoPareja.torneo_id == torneo_id
        ).first()
        
        if not pareja:
            raise HTTPException(status_code=404, detail="Pareja no encontrada")
        
        # Verificar que el usuario es parte de la pareja
        user_id = current_user.id_usuario
        if user_id not in [pareja.jugador1_id, pareja.jugador2_id]:
            raise HTTPException(status_code=403, detail="No tienes permisos para editar esta pareja")
        
        # Actualizar restricciones
        pareja.disponibilidad_horaria = restricciones.get('disponibilidad_horaria')
        db.commit()
        
        return {
            "mensaje": "Restricciones horarias actualizadas correctamente",
            "pareja_id": pareja_id,
            "disponibilidad_horaria": pareja.disponibilidad_horaria
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirmar-pareja/{codigo}")
async def confirmar_pareja_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Confirma una inscripción usando el código recibido
    """
    from ..services.torneo_confirmacion_service import TorneoConfirmacionService
    
    try:
        pareja = TorneoConfirmacionService.confirmar_por_codigo(
            db=db,
            codigo=codigo,
            user_id=current_user.id_usuario
        )
        return {
            "mensaje": "Inscripción confirmada exitosamente",
            "pareja_id": pareja.id,
            "torneo_id": pareja.torneo_id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/rechazar-invitacion/{pareja_id}")
async def rechazar_invitacion(
    pareja_id: int,
    motivo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Rechaza una invitación de pareja
    """
    from ..services.torneo_confirmacion_service import TorneoConfirmacionService
    
    try:
        TorneoConfirmacionService.rechazar_invitacion(
            db=db,
            pareja_id=pareja_id,
            user_id=current_user.id_usuario,
            motivo=motivo
        )
        return {"mensaje": "Invitación rechazada"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{torneo_id}/parejas")
def listar_parejas(
    torneo_id: int,
    estado: Optional[str] = None,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Lista todas las parejas inscritas en el torneo
    
    - **estado**: Filtrar por estado (inscripta, confirmada, baja)
    - **categoria_id**: Filtrar por categoría (opcional)
    """
    from ..models.torneo_models import TorneoPareja, TorneoCategoria
    from ..models.driveplus_models import PerfilUsuario
    
    try:
        # Query optimizada
        query = db.query(TorneoPareja).filter(TorneoPareja.torneo_id == torneo_id)
        
        if estado:
            query = query.filter(TorneoPareja.estado == estado)
        
        if categoria_id:
            query = query.filter(TorneoPareja.categoria_id == categoria_id)
        
        parejas = query.all()
        
        if not parejas:
            return []
        
        # PRE-CARGAR perfiles, usuarios y categorías (optimización)
        jugadores_ids = set()
        categoria_ids = set()
        for p in parejas:
            jugadores_ids.add(p.jugador1_id)
            jugadores_ids.add(p.jugador2_id)
            if p.categoria_id:
                categoria_ids.add(p.categoria_id)
        
        # Cargar perfiles
        perfiles = db.query(PerfilUsuario).filter(
            PerfilUsuario.id_usuario.in_(jugadores_ids)
        ).all()
        perfiles_dict = {p.id_usuario: p for p in perfiles}
        
        # Cargar usuarios para obtener nombre_usuario
        from ..models.driveplus_models import Usuario
        usuarios = db.query(Usuario).filter(
            Usuario.id_usuario.in_(jugadores_ids)
        ).all()
        usuarios_dict = {u.id_usuario: u for u in usuarios}
        
        categorias = db.query(TorneoCategoria).filter(
            TorneoCategoria.id.in_(categoria_ids)
        ).all() if categoria_ids else []
        categorias_dict = {c.id: c for c in categorias}
        
        resultado = []
        for pareja in parejas:
            perfil1 = perfiles_dict.get(pareja.jugador1_id)
            perfil2 = perfiles_dict.get(pareja.jugador2_id)
            usuario1 = usuarios_dict.get(pareja.jugador1_id)
            usuario2 = usuarios_dict.get(pareja.jugador2_id)
            categoria = categorias_dict.get(pareja.categoria_id) if pareja.categoria_id else None
            
            jugador1_nombre = f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Usuario {pareja.jugador1_id}"
            jugador2_nombre = f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Usuario {pareja.jugador2_id}"
            
            resultado.append({
                "id": pareja.id,
                "id_pareja": pareja.id,
                "torneo_id": pareja.torneo_id,
                "categoria_id": pareja.categoria_id,
                "categoria_nombre": categoria.nombre if categoria else None,
                "categoria_genero": categoria.genero if categoria else None,
                "jugador1_id": pareja.jugador1_id,
                "jugador2_id": pareja.jugador2_id,
                "jugador1_nombre": jugador1_nombre,
                "jugador2_nombre": jugador2_nombre,
                "jugador1_username": usuario1.nombre_usuario if usuario1 else None,
                "jugador2_username": usuario2.nombre_usuario if usuario2 else None,
                "nombre_pareja": f"{jugador1_nombre} / {jugador2_nombre}",
                "estado": pareja.estado.value if hasattr(pareja.estado, 'value') else str(pareja.estado).replace('EstadoPareja.', '').lower(),
                "categoria_asignada": pareja.categoria_asignada,
                "disponibilidad_horaria": pareja.disponibilidad_horaria,
                "created_at": pareja.created_at.isoformat() if pareja.created_at else None
            })
        
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def _pareja_to_dict(db: Session, pareja) -> dict:
    """Helper para convertir pareja a dict con nombres de jugadores"""
    from ..models.driveplus_models import PerfilUsuario
    perfil1 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador1_id).first()
    perfil2 = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == pareja.jugador2_id).first()
    jugador1_nombre = f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Usuario {pareja.jugador1_id}"
    jugador2_nombre = f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Usuario {pareja.jugador2_id}"
    return {
        "id": pareja.id,
        "id_pareja": pareja.id,
        "torneo_id": pareja.torneo_id,
        "jugador1_id": pareja.jugador1_id,
        "jugador2_id": pareja.jugador2_id,
        "jugador1_nombre": jugador1_nombre,
        "jugador2_nombre": jugador2_nombre,
        "nombre_pareja": f"{jugador1_nombre} / {jugador2_nombre}",
        "estado": pareja.estado.value if hasattr(pareja.estado, 'value') else str(pareja.estado),
        "categoria_asignada": pareja.categoria_asignada,
        "created_at": pareja.created_at.isoformat() if pareja.created_at else None
    }


@router.patch("/{torneo_id}/parejas/{pareja_id}/confirmar")
async def confirmar_pareja(
    torneo_id: int,
    pareja_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Confirma una pareja inscrita
    
    Solo organizadores pueden confirmar parejas
    """
    from ..services.torneo_inscripcion_service import TorneoInscripcionService
    
    try:
        user_id = current_user.id_usuario
        pareja = TorneoInscripcionService.confirmar_pareja(db, pareja_id, user_id)
        return _pareja_to_dict(db, pareja)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{torneo_id}/parejas/{pareja_id}/rechazar", status_code=status.HTTP_204_NO_CONTENT)
def rechazar_pareja(
    torneo_id: int,
    pareja_id: int,
    motivo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Rechaza/elimina una pareja inscrita
    
    Solo organizadores pueden rechazar parejas
    """
    from ..services.torneo_inscripcion_service import TorneoInscripcionService
    
    try:
        user_id = current_user.id_usuario
        TorneoInscripcionService.rechazar_pareja(db, pareja_id, user_id, motivo)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{torneo_id}/parejas/{pareja_id}/baja")
async def dar_baja_pareja(
    torneo_id: int,
    pareja_id: int,
    data: BajaParejaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Da de baja (elimina) una pareja
    
    Puede ser realizado por uno de los jugadores o por un organizador.
    La pareja se elimina completamente, permitiendo que se vuelvan a inscribir.
    """
    from ..services.torneo_inscripcion_service import TorneoInscripcionService
    
    try:
        user_id = current_user.id_usuario
        resultado = TorneoInscripcionService.dar_baja_pareja(db, pareja_id, user_id, data.motivo)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{torneo_id}/parejas/{pareja_id}/reemplazar-jugador")
def reemplazar_jugador(
    torneo_id: int,
    pareja_id: int,
    jugador_saliente_id: int,
    jugador_entrante_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Reemplaza un jugador en una pareja
    
    Solo organizadores pueden reemplazar jugadores
    """
    from ..services.torneo_inscripcion_service import TorneoInscripcionService
    
    try:
        user_id = current_user.id_usuario
        pareja = TorneoInscripcionService.reemplazar_jugador(
            db, pareja_id, jugador_saliente_id, jugador_entrante_id, user_id
        )
        return _pareja_to_dict(db, pareja)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{torneo_id}/parejas/{pareja_id}")
def actualizar_pareja(
    torneo_id: int,
    pareja_id: int,
    pareja_data: ParejaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza datos de una pareja
    
    Solo organizadores pueden actualizar parejas
    """
    from ..services.torneo_inscripcion_service import TorneoInscripcionService
    
    try:
        user_id = current_user.id_usuario
        pareja = TorneoInscripcionService.actualizar_pareja(db, pareja_id, pareja_data, user_id)
        return _pareja_to_dict(db, pareja)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================
# ENDPOINTS DE ZONAS
# ============================================

@router.post("/{torneo_id}/generar-zonas")
@router.post("/{torneo_id}/zonas/generar")  # Alias para compatibilidad con frontend
def generar_zonas(
    torneo_id: int,
    num_zonas: Optional[int] = None,
    balancear_por_rating: bool = True,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera zonas automáticamente y distribuye parejas
    
    Solo organizadores pueden generar zonas
    
    - **num_zonas**: Número de zonas (opcional, se calcula automáticamente)
    - **balancear_por_rating**: Si True, distribuye parejas por rating
    - **categoria_id**: ID de categoría (opcional, si se pasa genera solo para esa categoría)
    """
    from ..services.torneo_zona_service import TorneoZonaService
    
    try:
        user_id = current_user.id_usuario
        zonas = TorneoZonaService.generar_zonas_automaticas(
            db, torneo_id, user_id, num_zonas, balancear_por_rating, categoria_id
        )
        return {
            "message": "Zonas generadas exitosamente",
            "zonas": [{"id": z.id, "nombre": z.nombre, "numero": z.numero_orden, "categoria_id": z.categoria_id} for z in zonas]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{torneo_id}/zonas")
def listar_zonas(
    torneo_id: int,
    db: Session = Depends(get_db)
):
    """Lista todas las zonas del torneo con sus parejas"""
    from ..services.torneo_zona_service import TorneoZonaService
    from ..models.driveplus_models import PerfilUsuario
    
    try:
        zonas = TorneoZonaService.listar_zonas(db, torneo_id)
        
        # PRE-CARGAR todos los perfiles de una vez (optimización)
        jugadores_ids = set()
        for zona in zonas:
            if 'parejas' in zona:
                for pareja in zona['parejas']:
                    jugadores_ids.add(pareja['jugador1_id'])
                    jugadores_ids.add(pareja['jugador2_id'])
        
        # UNA SOLA QUERY para todos los perfiles
        perfiles = db.query(PerfilUsuario).filter(
            PerfilUsuario.id_usuario.in_(jugadores_ids)
        ).all() if jugadores_ids else []
        
        # Crear diccionario para acceso rápido
        perfiles_dict = {p.id_usuario: p for p in perfiles}
        
        # Agregar nombres usando el cache
        for zona in zonas:
            if 'parejas' in zona:
                for pareja in zona['parejas']:
                    perfil1 = perfiles_dict.get(pareja['jugador1_id'])
                    perfil2 = perfiles_dict.get(pareja['jugador2_id'])
                    
                    nombre1 = f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Jugador {pareja['jugador1_id']}"
                    nombre2 = f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Jugador {pareja['jugador2_id']}"
                    
                    pareja['pareja_nombre'] = f"{nombre1} / {nombre2}"
        
        return zonas
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{torneo_id}/zonas")
def eliminar_zonas(
    torneo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    categoria_id: Optional[int] = None
):
    """
    Elimina todas las zonas de un torneo o de una categoría específica.
    Solo organizadores pueden eliminar zonas.
    Query params: categoria_id (opcional)
    """
    from ..models.torneo_models import Torneo, TorneoZona, TorneoZonaPareja, TorneoTablaPosiciones
    from ..models.driveplus_models import Partido
    
    try:
        # Verificar permisos
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if not torneo:
            raise HTTPException(status_code=404, detail="Torneo no encontrado")
        
        if torneo.creado_por != current_user.id_usuario:
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        # Obtener zonas a eliminar
        query = db.query(TorneoZona).filter(TorneoZona.torneo_id == torneo_id)
        if categoria_id:
            query = query.filter(TorneoZona.categoria_id == categoria_id)
        
        zonas = query.all()
        zonas_ids = [z.id for z in zonas]
        
        if not zonas_ids:
            return {"message": "No hay zonas para eliminar", "zonas_eliminadas": 0}
        
        # Eliminar partidos
        db.query(Partido).filter(Partido.zona_id.in_(zonas_ids)).delete(synchronize_session=False)
        
        # Eliminar tablas de posiciones
        db.query(TorneoTablaPosiciones).filter(
            TorneoTablaPosiciones.zona_id.in_(zonas_ids)
        ).delete(synchronize_session=False)
        
        # Eliminar relaciones zona-pareja
        db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.zona_id.in_(zonas_ids)
        ).delete(synchronize_session=False)
        
        # Eliminar zonas
        db.query(TorneoZona).filter(TorneoZona.id.in_(zonas_ids)).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "message": "Zonas eliminadas exitosamente",
            "zonas_eliminadas": len(zonas_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{torneo_id}/zonas/tablas")
def listar_zonas_con_tablas(
    torneo_id: int,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Lista zonas con tablas OPTIMIZADO - carga todo en batch.
    Si categoria_id se pasa, solo zonas de esa categoría (más rápido).
    """
    from ..services.torneo_zona_service import TorneoZonaService
    from ..models.driveplus_models import PerfilUsuario, Partido, Usuario
    from ..models.torneo_models import TorneoZona, TorneoZonaPareja, TorneoPareja

    try:
        # 1. Obtener zonas
        zonas = TorneoZonaService.listar_zonas(db, torneo_id)
        if not zonas:
            return {"zonas": [], "tablas": []}
        
        if categoria_id is not None:
            zonas = [z for z in zonas if z.get("categoria_id") == categoria_id]
            if not zonas:
                return {"zonas": [], "tablas": []}

        zonas_ids = [z["id"] for z in zonas]

        # 2. Cargar TODAS las asignaciones de parejas a zonas en una sola query
        asignaciones = db.query(TorneoZonaPareja).filter(
            TorneoZonaPareja.zona_id.in_(zonas_ids)
        ).all()
        
        # Agrupar asignaciones por zona
        asignaciones_por_zona = {}
        parejas_ids = set()
        for asig in asignaciones:
            if asig.zona_id not in asignaciones_por_zona:
                asignaciones_por_zona[asig.zona_id] = []
            asignaciones_por_zona[asig.zona_id].append(asig)
            parejas_ids.add(asig.pareja_id)

        # 3. Cargar TODAS las parejas en una sola query
        parejas = db.query(TorneoPareja).filter(TorneoPareja.id.in_(parejas_ids)).all() if parejas_ids else []
        parejas_dict = {p.id: p for p in parejas}

        # 4. Cargar TODOS los partidos confirmados de estas zonas en una sola query
        partidos = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.zona_id.in_(zonas_ids),
            Partido.estado == 'confirmado'
        ).all()
        
        # Agrupar partidos por zona
        partidos_por_zona = {}
        jugadores_ids = set()
        for partido in partidos:
            if partido.zona_id not in partidos_por_zona:
                partidos_por_zona[partido.zona_id] = []
            partidos_por_zona[partido.zona_id].append(partido)

        # 5. Construir tablas en memoria
        tablas_result = []
        for zona in zonas:
            zona_id = zona["id"]
            tabla = []
            
            # Inicializar tabla con parejas de esta zona
            for asig in asignaciones_por_zona.get(zona_id, []):
                pareja = parejas_dict.get(asig.pareja_id)
                if pareja:
                    jugadores_ids.add(pareja.jugador1_id)
                    jugadores_ids.add(pareja.jugador2_id)
                    tabla.append({
                        'pareja_id': pareja.id,
                        'jugador1_id': pareja.jugador1_id,
                        'jugador2_id': pareja.jugador2_id,
                        'eliminada': False,
                        'partidos_jugados': 0,
                        'partidos_ganados': 0,
                        'partidos_perdidos': 0,
                        'sets_ganados': 0,
                        'sets_perdidos': 0,
                        'games_ganados': 0,
                        'games_perdidos': 0,
                        'puntos': 0
                    })
                else:
                    # Pareja eliminada
                    tabla.append({
                        'pareja_id': asig.pareja_id,
                        'jugador1_id': None,
                        'jugador2_id': None,
                        'eliminada': True,
                        'partidos_jugados': 0,
                        'partidos_ganados': 0,
                        'partidos_perdidos': 0,
                        'sets_ganados': 0,
                        'sets_perdidos': 0,
                        'games_ganados': 0,
                        'games_perdidos': 0,
                        'puntos': 0
                    })
            
            # Calcular estadísticas con partidos de esta zona
            for partido in partidos_por_zona.get(zona_id, []):
                pareja_a_id = partido.pareja1_id
                pareja_b_id = partido.pareja2_id
                
                if not pareja_a_id or not pareja_b_id:
                    continue
                
                idx_a = next((i for i, p in enumerate(tabla) if p['pareja_id'] == pareja_a_id), None)
                idx_b = next((i for i, p in enumerate(tabla) if p['pareja_id'] == pareja_b_id), None)
                
                if idx_a is None or idx_b is None:
                    continue
                
                tabla[idx_a]['partidos_jugados'] += 1
                tabla[idx_b]['partidos_jugados'] += 1
                
                if partido.resultado_padel:
                    resultado = partido.resultado_padel
                    sets = resultado.get('sets', [])
                    
                    sets_a = 0
                    sets_b = 0
                    games_a = 0
                    games_b = 0
                    
                    for set_data in sets:
                        if set_data.get('completado'):
                            games_eq_a = set_data.get('gamesEquipoA', 0)
                            games_eq_b = set_data.get('gamesEquipoB', 0)
                            
                            games_a += games_eq_a
                            games_b += games_eq_b
                            
                            if set_data.get('ganador') == 'equipoA':
                                sets_a += 1
                            elif set_data.get('ganador') == 'equipoB':
                                sets_b += 1
                    
                    tabla[idx_a]['sets_ganados'] += sets_a
                    tabla[idx_a]['sets_perdidos'] += sets_b
                    tabla[idx_a]['games_ganados'] += games_a
                    tabla[idx_a]['games_perdidos'] += games_b
                    
                    tabla[idx_b]['sets_ganados'] += sets_b
                    tabla[idx_b]['sets_perdidos'] += sets_a
                    tabla[idx_b]['games_ganados'] += games_b
                    tabla[idx_b]['games_perdidos'] += games_a
                    
                    if partido.ganador_pareja_id == pareja_a_id:
                        tabla[idx_a]['partidos_ganados'] += 1
                        tabla[idx_a]['puntos'] += 3
                        tabla[idx_b]['partidos_perdidos'] += 1
                    elif partido.ganador_pareja_id == pareja_b_id:
                        tabla[idx_b]['partidos_ganados'] += 1
                        tabla[idx_b]['puntos'] += 3
                        tabla[idx_a]['partidos_perdidos'] += 1
            
            # Ordenar tabla
            tabla.sort(key=lambda x: (
                -x['puntos'],
                -(x['sets_ganados'] - x['sets_perdidos']),
                -(x['games_ganados'] - x['games_perdidos'])
            ))
            
            # Agregar posición
            for i, item in enumerate(tabla, 1):
                item['posicion'] = i
            
            tablas_result.append({
                "zona_id": zona_id,
                "zona_nombre": zona["nombre"],
                "categoria_id": zona.get("categoria_id"),
                "tabla": tabla,
            })

        # 6. Cargar perfiles y usernames en una sola query
        usuarios = db.query(Usuario, PerfilUsuario).join(
            PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario, isouter=True
        ).filter(
            Usuario.id_usuario.in_(jugadores_ids)
        ).all() if jugadores_ids else []
        
        usuarios_dict = {}
        for usuario, perfil in usuarios:
            usuarios_dict[usuario.id_usuario] = {
                'nombre': perfil.nombre if perfil else None,
                'apellido': perfil.apellido if perfil else None,
                'username': usuario.nombre_usuario
            }

        # 7. Agregar nombres a las tablas
        for t in tablas_result:
            for item in t["tabla"]:
                if not item['eliminada']:
                    user1 = usuarios_dict.get(item.get("jugador1_id"))
                    user2 = usuarios_dict.get(item.get("jugador2_id"))
                    
                    if user1:
                        nombre1 = f"{user1['nombre']} {user1['apellido']}" if user1['nombre'] else f"Jugador {item['jugador1_id']}"
                        item["jugador1_nombre"] = nombre1
                        item["jugador1_username"] = user1['username']
                    
                    if user2:
                        nombre2 = f"{user2['nombre']} {user2['apellido']}" if user2['nombre'] else f"Jugador {item['jugador2_id']}"
                        item["jugador2_nombre"] = nombre2
                        item["jugador2_username"] = user2['username']
                    
                    if user1 and user2:
                        item["pareja_nombre"] = f"{item['jugador1_nombre']} / {item['jugador2_nombre']}"

        return {"zonas": zonas, "tablas": tablas_result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{torneo_id}/zonas/{zona_id}/tabla")
def obtener_tabla_zona(
    torneo_id: int,
    zona_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene la tabla de posiciones de una zona"""
    from ..services.torneo_zona_service import TorneoZonaService
    from ..models.driveplus_models import PerfilUsuario
    
    try:
        tabla = TorneoZonaService.obtener_tabla_posiciones(db, zona_id)
        
        # PRE-CARGAR todos los perfiles de una vez (optimización)
        jugadores_ids = set()
        for item in tabla['tabla']:
            jugadores_ids.add(item['jugador1_id'])
            jugadores_ids.add(item['jugador2_id'])
        
        # UNA SOLA QUERY para todos los perfiles
        perfiles = db.query(PerfilUsuario).filter(
            PerfilUsuario.id_usuario.in_(jugadores_ids)
        ).all() if jugadores_ids else []
        
        # Crear diccionario para acceso rápido
        perfiles_dict = {p.id_usuario: p for p in perfiles}
        
        # Agregar nombres usando el cache
        for item in tabla['tabla']:
            perfil1 = perfiles_dict.get(item['jugador1_id'])
            perfil2 = perfiles_dict.get(item['jugador2_id'])
            
            nombre1 = f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Jugador {item['jugador1_id']}"
            nombre2 = f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Jugador {item['jugador2_id']}"
            
            item['pareja_nombre'] = f"{nombre1} / {nombre2}"
        
        return tabla
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class CrearZonaRequest(BaseModel):
    """Body para crear una zona de último momento"""
    categoria_id: int
    nombre: str = "Zona último momento"
    pareja_ids: List[int]


@router.post("/{torneo_id}/zonas")
def crear_zona_ultimo_momento(
    torneo_id: int,
    body: CrearZonaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea una zona nueva en una categoría y asigna las parejas indicadas.
    Para zonas de último momento (parejas que se inscriben tarde).
    Solo organizadores. No disponible si ya se generaron playoffs.
    """
    from ..models.driveplus_models import Partido
    from ..models.torneo_models import Torneo
    from ..services.torneo_zona_service import TorneoZonaService

    try:
        # No permitir si ya hay playoffs
        partidos_playoff = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase.in_(['8vos', '4tos', 'semis', 'final', 'cuartos', 'semifinal'])
        ).limit(1).first()
        if partidos_playoff:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden agregar zonas si ya se generaron los playoffs"
            )
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if not torneo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Torneo no encontrado")

        zona = TorneoZonaService.crear_zona_ultimo_momento(
            db, torneo_id, body.categoria_id, body.nombre, body.pareja_ids, current_user.id_usuario
        )
        return {
            "message": "Zona creada. Generá los partidos de esta zona desde Programación.",
            "zona": {"id": zona.id, "nombre": zona.nombre, "categoria_id": zona.categoria_id}
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{torneo_id}/zonas/{zona_id}/generar-partidos")
def generar_partidos_zona(
    torneo_id: int,
    zona_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera solo los partidos (round-robin) de una zona, sin borrar partidos existentes.
    Los partidos quedan sin fecha/cancha para asignarlos desde Programación.
    Solo organizadores.
    """
    from ..models.torneo_models import TorneoZona, TorneoZonaPareja, TorneoPareja, Torneo
    from ..models.driveplus_models import Partido

    from ..services.torneo_zona_service import TorneoZonaService
    from ..services.torneo_fixture_global_service import TorneoFixtureGlobalService

    try:
        if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos")
        zona = db.query(TorneoZona).filter(
            TorneoZona.id == zona_id,
            TorneoZona.torneo_id == torneo_id
        ).first()
        if not zona:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")

        partidos_dict = TorneoFixtureGlobalService._generar_partidos_zona(db, zona)
        if not partidos_dict:
            return {"message": "La zona no tiene al menos 2 parejas", "partidos_creados": 0}

        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        # Batch: cargar partidos existentes de la zona (evitar N+1)
        existentes = db.query(Partido.pareja1_id, Partido.pareja2_id).filter(
            Partido.id_torneo == torneo_id,
            Partido.zona_id == zona_id
        ).all()
        existentes_set = {(r.pareja1_id, r.pareja2_id) for r in existentes}
        creados = 0
        for p in partidos_dict:
            key = (p['pareja1_id'], p['pareja2_id'])
            if key in existentes_set:
                continue
            existentes_set.add(key)
            partido = Partido(
                id_torneo=torneo_id,
                zona_id=zona_id,
                categoria_id=zona.categoria_id,
                fase='zona',
                pareja1_id=p['pareja1_id'],
                pareja2_id=p['pareja2_id'],
                estado='pendiente',
                tipo='torneo',
                id_creador=torneo.creado_por if torneo else current_user.id_usuario,
            )
            db.add(partido)
            creados += 1
        db.commit()
        return {"message": f"Partidos de la zona creados ({creados})", "partidos_creados": creados}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{torneo_id}/zonas/mover-pareja")
def mover_pareja(
    torneo_id: int,
    pareja_id: int,
    zona_destino_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Mueve una pareja de una zona a otra
    
    Solo organizadores pueden mover parejas
    """
    from ..services.torneo_zona_service import TorneoZonaService
    
    try:
        user_id = current_user.id_usuario
        result = TorneoZonaService.mover_pareja_entre_zonas(
            db, pareja_id, zona_destino_id, user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================
# ENDPOINTS DE FIXTURE
# ============================================

@router.post("/{torneo_id}/generar-zonas-inteligente")
def generar_zonas_inteligente(
    torneo_id: int,
    num_zonas: Optional[int] = None,
    num_canchas: int = 3,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera zonas considerando disponibilidad horaria y balanceo por rating
    
    Prioridad 1: Compatibilidad horaria entre parejas de la misma zona
    Prioridad 2: Balanceo por rating
    
    Parámetros:
    - num_zonas: Número de zonas (opcional, se calcula automáticamente)
    - num_canchas: Número de canchas disponibles (default: 3)
    - categoria_id: ID de categoría (opcional)
    
    Solo organizadores pueden generar zonas
    """
    from ..services.torneo_zona_horarios_service import TorneoZonaHorariosService
    
    try:
        user_id = current_user.id_usuario
        resultado = TorneoZonaHorariosService.generar_zonas_con_horarios(
            db, torneo_id, user_id, num_zonas, num_canchas, categoria_id
        )
        return {
            "message": "Zonas generadas con criterio de disponibilidad horaria",
            "zonas_creadas": resultado["zonas_creadas"],
            "zonas": resultado["zonas"],
            "compatibilidad_promedio": f"{resultado['compatibilidad_promedio'] * 100:.1f}%"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{torneo_id}/generar-fixture")
def generar_fixture(
    torneo_id: int,
    categoria_id: Optional[int] = Query(None, description="ID de categoría para generar fixture solo de esa categoría"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera el fixture completo del torneo o de una categoría específica
    
    Parámetros:
    - categoria_id (opcional): Si se especifica, solo genera fixture para esa categoría
    
    Consideraciones:
    - Todas las zonas y categorías (o solo la especificada)
    - Disponibilidad horaria de parejas
    - Canchas disponibles (no más partidos simultáneos que canchas)
    - Duración de partidos: 50 minutos
    
    Solo organizadores pueden generar fixture
    """
    from ..services.torneo_fixture_global_service import TorneoFixtureGlobalService
    
    try:
        user_id = current_user.id_usuario
        resultado = TorneoFixtureGlobalService.generar_fixture_completo(
            db, torneo_id, user_id, categoria_id
        )
        
        response = {
            "message": f"Fixture generado exitosamente{' para categoría ' + str(categoria_id) if categoria_id else ''}",
            "partidos_generados": resultado["partidos_generados"],
            "partidos_no_programados": resultado["partidos_no_programados"],
            "zonas_procesadas": resultado["zonas_procesadas"],
            "canchas_utilizadas": resultado["canchas_utilizadas"],
            "slots_utilizados": resultado["slots_utilizados"]
        }
        
        # Incluir detalles de partidos no programados si existen
        if resultado["partidos_sin_programar"]:
            response["partidos_sin_programar"] = resultado["partidos_sin_programar"]
            response["warning"] = f"⚠️ {resultado['partidos_no_programados']} partidos no pudieron programarse por incompatibilidad horaria"
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{torneo_id}/fixture")
def eliminar_fixture(
    torneo_id: int,
    categoria_id: Optional[int] = Query(None, description="ID de categoría para eliminar fixture solo de esa categoría"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina partidos de fase de grupos del torneo.
    
    Parámetros:
    - categoria_id (opcional): Si se especifica, solo elimina partidos de esa categoría
    
    Solo organizadores pueden eliminar fixture.
    """
    from ..models.torneo_models import Torneo
    from ..models.driveplus_models import Partido
    
    try:
        # Verificar permisos
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if not torneo:
            raise HTTPException(status_code=404, detail="Torneo no encontrado")
        
        if torneo.creado_por != current_user.id_usuario:
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        # Construir query base
        query = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase == 'zona'
        )
        
        # Filtrar por categoría si se especifica
        if categoria_id:
            query = query.filter(Partido.categoria_id == categoria_id)
        
        # Eliminar partidos
        partidos_eliminados = query.delete(synchronize_session=False)
        
        db.commit()
        
        mensaje = f"Fixture eliminado exitosamente"
        if categoria_id:
            mensaje += f" para categoría {categoria_id}"
        
        return {
            "message": mensaje,
            "partidos_eliminados": partidos_eliminados
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{torneo_id}/partidos")
def listar_partidos_torneo(
    torneo_id: int,
    zona_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Lista todos los partidos del torneo
    
    - **zona_id**: Filtrar por zona (opcional)
    - **categoria_id**: Filtrar por categoría (opcional)
    """
    from ..models.driveplus_models import Partido, PerfilUsuario
    from ..models.torneo_models import TorneoPareja
    
    try:
        query = db.query(Partido).filter(Partido.id_torneo == torneo_id)
        
        if zona_id is not None:
            query = query.filter(Partido.zona_id == zona_id)
        
        if categoria_id is not None:
            query = query.filter(Partido.categoria_id == categoria_id)
        
        partidos = query.all()
        
        if not partidos:
            return {"total": 0, "partidos": []}
        
        # PRE-CARGAR todas las parejas del torneo (optimización)
        parejas = db.query(TorneoPareja).filter(TorneoPareja.torneo_id == torneo_id).all()
        parejas_dict = {p.id: p for p in parejas}
        
        # PRE-CARGAR todos los perfiles de jugadores involucrados
        jugadores_ids = set()
        for p in parejas:
            jugadores_ids.add(p.jugador1_id)
            jugadores_ids.add(p.jugador2_id)
        
        perfiles = db.query(PerfilUsuario).filter(
            PerfilUsuario.id_usuario.in_(jugadores_ids)
        ).all() if jugadores_ids else []
        perfiles_dict = {p.id_usuario: p for p in perfiles}
        
        # Helper para obtener nombre de pareja
        def get_nombre_pareja(pareja_id):
            if not pareja_id:
                return "TBD"
            pareja = parejas_dict.get(pareja_id)
            if not pareja:
                return "TBD"
            p1 = perfiles_dict.get(pareja.jugador1_id)
            p2 = perfiles_dict.get(pareja.jugador2_id)
            n1 = f"{p1.nombre} {p1.apellido}" if p1 else f"Jugador {pareja.jugador1_id}"
            n2 = f"{p2.nombre} {p2.apellido}" if p2 else f"Jugador {pareja.jugador2_id}"
            return f"{n1} / {n2}"
        
        resultado = [
            {
                "id_partido": p.id_partido,
                "pareja1_id": p.pareja1_id,
                "pareja2_id": p.pareja2_id,
                "pareja1_nombre": get_nombre_pareja(p.pareja1_id),
                "pareja2_nombre": get_nombre_pareja(p.pareja2_id),
                "pareja1_disponibilidad": parejas_dict.get(p.pareja1_id).disponibilidad_horaria if p.pareja1_id and parejas_dict.get(p.pareja1_id) else None,
                "pareja2_disponibilidad": parejas_dict.get(p.pareja2_id).disponibilidad_horaria if p.pareja2_id and parejas_dict.get(p.pareja2_id) else None,
                "zona_id": p.zona_id,
                "categoria_id": getattr(p, 'categoria_id', None),
                "fase": p.fase,
                "estado": p.estado,
                "fecha_hora": p.fecha_hora.isoformat() if p.fecha_hora else None,
                "cancha_id": p.cancha_id,
                "ganador_pareja_id": p.ganador_pareja_id,
                "resultado_padel": p.resultado_padel
            }
            for p in partidos
        ]
        
        return {"total": len(resultado), "partidos": resultado}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================
# ENDPOINTS DE RESULTADOS
# ============================================

@router.post("/{torneo_id}/partidos/{partido_id}/resultado")
def cargar_resultado_partido(
    torneo_id: int,
    partido_id: int,
    resultado: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Carga el resultado de un partido de torneo
    
    El resultado debe incluir:
    - sets: Lista de sets con gamesEquipoA, gamesEquipoB, ganador
    - Mínimo 2 sets, máximo 3
    - Un equipo debe ganar al menos 2 sets
    
    Solo organizadores pueden cargar resultados
    """
    from ..services.torneo_resultado_service import TorneoResultadoService
    
    try:
        user_id = current_user.id_usuario
        partido = TorneoResultadoService.cargar_resultado(
            db, partido_id, resultado, user_id
        )
        return {
            "message": "Resultado cargado exitosamente",
            "partido_id": partido.id_partido,
            "ganador_pareja_id": partido.ganador_pareja_id,
            "elo_aplicado": partido.elo_aplicado
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{torneo_id}/partidos/{partido_id}/resultado")
def corregir_resultado_partido(
    torneo_id: int,
    partido_id: int,
    resultado: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Corrige el resultado de un partido ya finalizado
    
    Solo organizadores pueden corregir resultados
    """
    from ..services.torneo_resultado_service import TorneoResultadoService
    
    try:
        user_id = current_user.id_usuario
        partido = TorneoResultadoService.corregir_resultado(
            db, partido_id, resultado, user_id
        )
        return {
            "message": "Resultado corregido exitosamente",
            "partido_id": partido.id_partido,
            "ganador_pareja_id": partido.ganador_pareja_id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{torneo_id}/partidos/{partido_id}/estadisticas")
def obtener_estadisticas_partido(
    torneo_id: int,
    partido_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas detalladas de un partido"""
    from ..services.torneo_resultado_service import TorneoResultadoService
    
    try:
        estadisticas = TorneoResultadoService.obtener_estadisticas_partido(db, partido_id)
        return estadisticas
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{torneo_id}/zonas/{zona_id}/clasificados")
def obtener_clasificados_zona(
    torneo_id: int,
    zona_id: int,
    num_clasificados: int = 2,
    db: Session = Depends(get_db)
):
    """
    Obtiene las parejas clasificadas de una zona
    
    - **num_clasificados**: Número de parejas que clasifican (default: 2)
    """
    from ..services.torneo_resultado_service import TorneoResultadoService
    
    try:
        clasificados = TorneoResultadoService.obtener_clasificados_zona(
            db, zona_id, num_clasificados
        )
        return {
            "zona_id": zona_id,
            "num_clasificados": num_clasificados,
            "clasificados": clasificados
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{torneo_id}/zonas/{zona_id}/completa")
def verificar_zona_completa(
    torneo_id: int,
    zona_id: int,
    db: Session = Depends(get_db)
):
    """Verifica si todos los partidos de una zona están finalizados"""
    from ..services.torneo_resultado_service import TorneoResultadoService
    
    try:
        completa = TorneoResultadoService.verificar_zona_completa(db, zona_id)
        return {
            "zona_id": zona_id,
            "completa": completa
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================
# ENDPOINTS DE PLAYOFFS
# ============================================

@router.post("/{torneo_id}/generar-playoffs")
def generar_playoffs(
    torneo_id: int,
    clasificados_por_zona: int = 2,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera el cuadro de playoffs automáticamente.
    Igual que el fixture: se puede generar por categoría o todas.
    
    Solo organizadores pueden generar playoffs.
    El torneo debe estar en fase de grupos.
    
    - **clasificados_por_zona**: Número de clasificados por zona (default: 2)
    - **categoria_id**: Si se pasa, solo genera playoffs para esa categoría
    """
    from ..services.torneo_playoff_service import TorneoPlayoffService
    
    try:
        user_id = current_user.id_usuario
        partidos = TorneoPlayoffService.generar_playoffs(
            db, torneo_id, user_id, clasificados_por_zona, categoria_id
        )
        return {
            "message": "Playoffs generados exitosamente",
            "total_partidos": len(partidos),
            "partidos": [
                {
                    "id": p.id_partido,
                    "fase": p.fase.value if hasattr(p.fase, 'value') else str(p.fase),
                    "numero_partido": p.numero_partido,
                    "pareja1_id": p.pareja1_id,
                    "pareja2_id": p.pareja2_id
                }
                for p in partidos
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class IntercambiarParejasPlayoffRequest(BaseModel):
    """Intercambiar una pareja de un cruce con una pareja de otro cruce (solo partidos pendientes)."""
    partido_id_a: int
    partido_id_b: int
    slot_a: int  # 1 = pareja1, 2 = pareja2
    slot_b: int  # 1 = pareja1, 2 = pareja2


class IntercambiarPartidosPlayoffRequest(BaseModel):
    """Intercambiar posiciones de dos partidos (cuadros) en el bracket. Intercambia numero_partido."""
    partido_id_a: int
    partido_id_b: int


@router.delete("/{torneo_id}/playoffs")
def eliminar_playoffs(
    torneo_id: int,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina los partidos de playoffs del torneo (o solo de una categoría).
    Solo organizadores. Permite volver a generar playoffs después.
    """
    from ..services.torneo_playoff_service import TorneoPlayoffService

    try:
        count = TorneoPlayoffService.eliminar_playoffs(
            db, torneo_id, current_user.id_usuario, categoria_id
        )
        return {"message": "Playoffs eliminados", "eliminados": count}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{torneo_id}/playoffs/intercambiar-parejas")
def intercambiar_parejas_playoff(
    torneo_id: int,
    body: IntercambiarParejasPlayoffRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Intercambia parejas entre dos cruces de playoff.
    Solo organizadores. Solo partidos pendientes (no confirmados ni BYE).
    """
    from ..services.torneo_playoff_service import TorneoPlayoffService
    from ..models.driveplus_models import Partido

    if not TorneoPlayoffService._es_organizador(db, torneo_id, current_user.id_usuario):
        raise HTTPException(status_code=403, detail="Solo organizadores pueden intercambiar parejas")
    if body.slot_a not in (1, 2) or body.slot_b not in (1, 2):
        raise HTTPException(status_code=400, detail="slot_a y slot_b deben ser 1 o 2")

    pa = db.query(Partido).filter(
        Partido.id_partido == body.partido_id_a,
        Partido.id_torneo == torneo_id,
        Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final'])
    ).first()
    pb = db.query(Partido).filter(
        Partido.id_partido == body.partido_id_b,
        Partido.id_torneo == torneo_id,
        Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final'])
    ).first()
    if not pa or not pb:
        raise HTTPException(status_code=404, detail="Uno o ambos partidos no existen o no son de playoff")
    if pa.categoria_id != pb.categoria_id:
        raise HTTPException(status_code=400, detail="Los partidos deben ser de la misma categoría")
    if pa.estado not in ('pendiente',) or pb.estado not in ('pendiente',):
        raise HTTPException(status_code=400, detail="Solo se pueden intercambiar parejas en partidos pendientes")

    id_a = pa.pareja1_id if body.slot_a == 1 else pa.pareja2_id
    id_b = pb.pareja1_id if body.slot_b == 1 else pb.pareja2_id
    if body.slot_a == 1:
        pa.pareja1_id = id_b
    else:
        pa.pareja2_id = id_b
    if body.slot_b == 1:
        pb.pareja1_id = id_a
    else:
        pb.pareja2_id = id_a
    db.commit()
    return {"message": "Parejas intercambiadas correctamente"}


@router.post("/{torneo_id}/playoffs/intercambiar-partidos")
def intercambiar_partidos_playoff(
    torneo_id: int,
    body: IntercambiarPartidosPlayoffRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Intercambia las posiciones de dos partidos en el bracket (swap de numero_partido).
    Así un cuadro completo sube o baja. Misma fase y misma categoría. Solo organizadores.
    """
    from ..services.torneo_playoff_service import TorneoPlayoffService
    from ..models.driveplus_models import Partido

    if not TorneoPlayoffService._es_organizador(db, torneo_id, current_user.id_usuario):
        raise HTTPException(status_code=403, detail="Solo organizadores pueden intercambiar partidos")

    pa = db.query(Partido).filter(
        Partido.id_partido == body.partido_id_a,
        Partido.id_torneo == torneo_id,
        Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final'])
    ).first()
    pb = db.query(Partido).filter(
        Partido.id_partido == body.partido_id_b,
        Partido.id_torneo == torneo_id,
        Partido.fase.in_(['16avos', '8vos', '4tos', 'cuartos', 'semis', 'semifinal', 'final'])
    ).first()
    if not pa or not pb:
        raise HTTPException(status_code=404, detail="Uno o ambos partidos no existen o no son de playoff")
    if pa.fase != pb.fase:
        raise HTTPException(status_code=400, detail="Solo se pueden intercambiar partidos de la misma fase")
    if pa.categoria_id != pb.categoria_id:
        raise HTTPException(status_code=400, detail="Los partidos deben ser de la misma categoría")

    na, nb = pa.numero_partido, pb.numero_partido
    pa.numero_partido = nb
    pb.numero_partido = na
    db.commit()
    return {"message": "Posiciones de cuadros intercambiadas correctamente"}


@router.get("/{torneo_id}/playoffs")
def listar_partidos_playoffs(
    torneo_id: int,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Lista todos los partidos de playoffs agrupados por fase y categoría
    
    - **categoria_id**: Filtrar por categoría específica (opcional)
    
    Si no se especifica categoria_id, devuelve playoffs agrupados por categoría
    """
    from ..services.torneo_playoff_service import TorneoPlayoffService
    from ..models.driveplus_models import PerfilUsuario
    from ..models.torneo_models import TorneoPareja, TorneoCategoria
    
    try:
        if categoria_id:
            # Caso específico: una sola categoría
            partidos_por_fase = TorneoPlayoffService.listar_partidos_playoffs(db, torneo_id, categoria_id)
            
            # PRE-CARGAR parejas y perfiles (optimización)
            parejas = db.query(TorneoPareja).filter(TorneoPareja.torneo_id == torneo_id).all()
            parejas_dict = {p.id: p for p in parejas}
            
            jugadores_ids = set()
            for p in parejas:
                jugadores_ids.add(p.jugador1_id)
                jugadores_ids.add(p.jugador2_id)
            
            perfiles = db.query(PerfilUsuario).filter(
                PerfilUsuario.id_usuario.in_(jugadores_ids)
            ).all() if jugadores_ids else []
            perfiles_dict = {p.id_usuario: p for p in perfiles}
            
            def get_nombre_pareja(pareja_id):
                if not pareja_id:
                    return None
                pareja = parejas_dict.get(pareja_id)
                if not pareja:
                    return None
                p1 = perfiles_dict.get(pareja.jugador1_id)
                p2 = perfiles_dict.get(pareja.jugador2_id)
                n1 = f"{p1.nombre} {p1.apellido}" if p1 else f"Jugador {pareja.jugador1_id}"
                n2 = f"{p2.nombre} {p2.apellido}" if p2 else f"Jugador {pareja.jugador2_id}"
                return f"{n1} / {n2}"
            
            resultado = {}
            for fase, partidos in partidos_por_fase.items():
                resultado[fase] = [
                    {
                        "id": p.id_partido,
                        "numero_partido": p.numero_partido,
                        "pareja1_id": p.pareja1_id,
                        "pareja2_id": p.pareja2_id,
                        "pareja1_nombre": get_nombre_pareja(p.pareja1_id),
                        "pareja2_nombre": get_nombre_pareja(p.pareja2_id),
                        "ganador_id": p.ganador_pareja_id,
                        "resultado": p.resultado_padel,
                        "fase": fase,
                        "categoria_id": getattr(p, 'categoria_id', None),
                        "estado": p.estado.value if hasattr(p.estado, 'value') else str(p.estado)
                    }
                    for p in partidos
                ]
            
            todos_partidos = []
            for partidos_fase in resultado.values():
                todos_partidos.extend(partidos_fase)
            
            return {"partidos": todos_partidos, "por_fase": resultado}
        
        else:
            # Caso general: todas las categorías, agrupadas por categoría
            categorias = db.query(TorneoCategoria).filter(
                TorneoCategoria.torneo_id == torneo_id
            ).all()
            
            if not categorias:
                # Sin categorías, usar el método original
                return listar_partidos_playoffs(torneo_id, None, db)
            
            resultado_por_categoria = {}
            
            for categoria in categorias:
                partidos_categoria = TorneoPlayoffService.listar_partidos_playoffs(db, torneo_id, categoria.id)
                
                if partidos_categoria:  # Solo incluir si hay partidos
                    resultado_por_categoria[categoria.nombre] = {
                        "categoria_id": categoria.id,
                        "categoria_nombre": categoria.nombre,
                        "genero": categoria.genero,
                        "partidos_por_fase": partidos_categoria,
                        "total_partidos": sum(len(partidos) for partidos in partidos_categoria.values())
                    }
            
            return {
                "por_categoria": resultado_por_categoria,
                "mensaje": "Playoffs separados por categoría. Use categoria_id para obtener una categoría específica."
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{torneo_id}/playoffs/partidos")
def listar_todos_partidos_playoffs(
    torneo_id: int,
    db: Session = Depends(get_db)
):
    """
    Lista todos los partidos de playoffs en una sola lista (sin agrupar)
    """
    from ..models.torneo_models import FasePartido, TorneoPareja
    from ..models.driveplus_models import Partido, PerfilUsuario
    
    try:
        partidos = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.fase != FasePartido.ZONA.value
        ).order_by(Partido.numero_partido).all()
        
        if not partidos:
            return {"total": 0, "partidos": []}
        
        # PRE-CARGAR parejas y perfiles (optimización)
        parejas = db.query(TorneoPareja).filter(TorneoPareja.torneo_id == torneo_id).all()
        parejas_dict = {p.id: p for p in parejas}
        
        jugadores_ids = set()
        for p in parejas:
            jugadores_ids.add(p.jugador1_id)
            jugadores_ids.add(p.jugador2_id)
        
        perfiles = db.query(PerfilUsuario).filter(
            PerfilUsuario.id_usuario.in_(jugadores_ids)
        ).all() if jugadores_ids else []
        perfiles_dict = {p.id_usuario: p for p in perfiles}
        
        def get_nombre_pareja(pareja_id):
            if not pareja_id:
                return None
            pareja = parejas_dict.get(pareja_id)
            if not pareja:
                return None
            p1 = perfiles_dict.get(pareja.jugador1_id)
            p2 = perfiles_dict.get(pareja.jugador2_id)
            n1 = f"{p1.nombre} {p1.apellido}" if p1 else f"Jugador {pareja.jugador1_id}"
            n2 = f"{p2.nombre} {p2.apellido}" if p2 else f"Jugador {pareja.jugador2_id}"
            return f"{n1} / {n2}"
        
        resultado = [
            {
                "id": p.id_partido,
                "numero_partido": p.numero_partido,
                "pareja1_id": p.pareja1_id,
                "pareja2_id": p.pareja2_id,
                "pareja1_nombre": get_nombre_pareja(p.pareja1_id),
                "pareja2_nombre": get_nombre_pareja(p.pareja2_id),
                "ganador_id": p.ganador_pareja_id,
                "resultado": p.resultado_padel,
                "fase": p.fase,
                "categoria_id": getattr(p, 'categoria_id', None),
                "estado": p.estado
            }
            for p in partidos
        ]
        
        return {"total": len(resultado), "partidos": resultado}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================
# ENDPOINTS DE CANCHAS Y PROGRAMACIÓN
# ============================================

class CanchaCreate(BaseModel):
    nombre: str
    activa: bool = True

@router.post("/{torneo_id}/canchas")
def crear_cancha(
    torneo_id: int,
    cancha_data: CanchaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea una cancha para el torneo
    
    Solo organizadores pueden crear canchas
    
    Body:
    - nombre: Nombre de la cancha
    - activa: Si está activa (default: true)
    """
    from ..models.torneo_models import TorneoCancha
    from ..services.torneo_zona_service import TorneoZonaService
    
    try:
        if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        cancha = TorneoCancha(
            torneo_id=torneo_id,
            nombre=cancha_data.nombre,
            activa=cancha_data.activa
        )
        db.add(cancha)
        db.commit()
        db.refresh(cancha)
        
        return {
            "id": cancha.id,
            "torneo_id": cancha.torneo_id,
            "nombre": cancha.nombre,
            "activa": cancha.activa
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{torneo_id}/canchas")
def listar_canchas(
    torneo_id: int,
    db: Session = Depends(get_db)
):
    """Lista todas las canchas del torneo"""
    from ..models.torneo_models import TorneoCancha
    
    canchas = db.query(TorneoCancha).filter(
        TorneoCancha.torneo_id == torneo_id,
        TorneoCancha.activa == True
    ).all()
    
    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "activa": c.activa
        }
        for c in canchas
    ]


@router.delete("/{torneo_id}/canchas/{cancha_id}")
def eliminar_cancha(
    torneo_id: int,
    cancha_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Desactiva una cancha"""
    from ..models.torneo_models import TorneoCancha
    from ..services.torneo_zona_service import TorneoZonaService
    
    if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    cancha = db.query(TorneoCancha).filter(
        TorneoCancha.id == cancha_id,
        TorneoCancha.torneo_id == torneo_id
    ).first()
    
    if not cancha:
        raise HTTPException(status_code=404, detail="Cancha no encontrada")
    
    cancha.activa = False
    db.commit()
    
    return {"message": "Cancha eliminada"}


@router.post("/{torneo_id}/slots")
def crear_slots(
    torneo_id: int,
    fecha: str,
    hora_inicio: str,
    hora_fin: str,
    duracion_minutos: int = 90,
    cancha_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea slots de horarios para un día
    
    - **fecha**: Fecha en formato YYYY-MM-DD
    - **hora_inicio**: Hora de inicio (ej: "09:00")
    - **hora_fin**: Hora de fin (ej: "21:00")
    - **duracion_minutos**: Duración de cada slot (default 90 min)
    - **cancha_ids**: Lista de canchas (opcional, si no se especifica usa todas)
    """
    from ..models.torneo_models import TorneoCancha, TorneoSlot
    from ..services.torneo_zona_service import TorneoZonaService
    from datetime import datetime, timedelta
    
    try:
        if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        # Parsear fecha y horas
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        hora_inicio_parts = hora_inicio.split(":")
        hora_fin_parts = hora_fin.split(":")
        
        hora_actual = datetime.combine(
            fecha_dt,
            datetime.strptime(hora_inicio, "%H:%M").time()
        )
        hora_limite = datetime.combine(
            fecha_dt,
            datetime.strptime(hora_fin, "%H:%M").time()
        )
        
        # Obtener canchas
        if cancha_ids:
            canchas = db.query(TorneoCancha).filter(
                TorneoCancha.id.in_(cancha_ids),
                TorneoCancha.torneo_id == torneo_id,
                TorneoCancha.activa == True
            ).all()
        else:
            canchas = db.query(TorneoCancha).filter(
                TorneoCancha.torneo_id == torneo_id,
                TorneoCancha.activa == True
            ).all()
        
        if not canchas:
            raise HTTPException(status_code=400, detail="No hay canchas disponibles")
        
        # Cargar slots existentes del día (evitar N+1)
        cancha_ids = [c.id for c in canchas]
        hora_inicio_dia = hora_actual
        existentes = db.query(TorneoSlot.cancha_id, TorneoSlot.fecha_hora_inicio).filter(
            TorneoSlot.torneo_id == torneo_id,
            TorneoSlot.cancha_id.in_(cancha_ids),
            TorneoSlot.fecha_hora_inicio >= hora_inicio_dia,
            TorneoSlot.fecha_hora_inicio <= hora_limite
        ).all()
        slots_existentes = {(r.cancha_id, r.fecha_hora_inicio) for r in existentes}
        
        slots_creados = 0
        while hora_actual + timedelta(minutes=duracion_minutos) <= hora_limite:
            for cancha in canchas:
                if (cancha.id, hora_actual) in slots_existentes:
                    continue
                slots_existentes.add((cancha.id, hora_actual))
                slot = TorneoSlot(
                    torneo_id=torneo_id,
                    cancha_id=cancha.id,
                    fecha_hora_inicio=hora_actual,
                    fecha_hora_fin=hora_actual + timedelta(minutes=duracion_minutos),
                    ocupado=False
                )
                db.add(slot)
                slots_creados += 1
            
            hora_actual += timedelta(minutes=duracion_minutos)
        
        db.commit()
        
        return {
            "message": f"Se crearon {slots_creados} slots",
            "fecha": fecha,
            "canchas": len(canchas),
            "slots_por_cancha": slots_creados // len(canchas) if canchas else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{torneo_id}/slots")
def listar_slots(
    torneo_id: int,
    fecha: Optional[str] = None,
    solo_disponibles: bool = False,
    db: Session = Depends(get_db)
):
    """
    Lista slots de horarios
    
    - **fecha**: Filtrar por fecha (YYYY-MM-DD)
    - **solo_disponibles**: Solo mostrar slots no ocupados
    """
    from ..models.torneo_models import TorneoSlot, TorneoCancha
    from datetime import datetime
    
    query = db.query(TorneoSlot).filter(TorneoSlot.torneo_id == torneo_id)
    
    if fecha:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        query = query.filter(
            TorneoSlot.fecha_hora_inicio >= datetime.combine(fecha_dt, datetime.min.time()),
            TorneoSlot.fecha_hora_inicio < datetime.combine(fecha_dt, datetime.max.time())
        )
    
    if solo_disponibles:
        query = query.filter(TorneoSlot.ocupado == False)
    
    slots = query.order_by(TorneoSlot.fecha_hora_inicio, TorneoSlot.cancha_id).all()
    
    # PRE-CARGAR todas las canchas de una vez (optimización)
    canchas = db.query(TorneoCancha).filter(TorneoCancha.torneo_id == torneo_id).all()
    canchas_dict = {c.id: c.nombre for c in canchas}
    
    resultado = [
        {
            "id": s.id,
            "cancha_id": s.cancha_id,
            "cancha_nombre": canchas_dict.get(s.cancha_id),
            "fecha_hora_inicio": s.fecha_hora_inicio.isoformat() if s.fecha_hora_inicio else None,
            "fecha_hora_fin": s.fecha_hora_fin.isoformat() if s.fecha_hora_fin else None,
            "ocupado": s.ocupado,
            "partido_id": s.partido_id
        }
        for s in slots
    ]
    
    return resultado


class ProgramacionParams(BaseModel):
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    duracion_partido_minutos: int = 70
    # Horarios para días de semana (Lun-Vie)
    hora_inicio_semana: Optional[str] = "17:00"
    hora_fin_semana: Optional[str] = "22:00"
    # Horarios para fin de semana (Sab-Dom)
    hora_inicio_finde: Optional[str] = "09:00"
    hora_fin_finde: Optional[str] = "21:00"


@router.delete("/{torneo_id}/limpiar-programacion")
def limpiar_programacion(
    torneo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Limpia toda la programación del torneo:
    - Elimina todos los slots
    - Desprograma todos los partidos (quita fecha_hora y cancha_id)
    
    Solo organizadores pueden limpiar la programación
    """
    from ..models.torneo_models import TorneoSlot
    from ..models.driveplus_models import Partido
    from ..services.torneo_zona_service import TorneoZonaService
    
    try:
        if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        # Contar antes de borrar
        slots_count = db.query(TorneoSlot).filter(TorneoSlot.torneo_id == torneo_id).count()
        
        # Desprogramar partidos (quitar fecha y cancha, pero no borrarlos)
        partidos_desprogramados = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.cancha_id != None
        ).update({
            "cancha_id": None,
            "fecha_hora": None
        }, synchronize_session=False)
        
        # Eliminar todos los slots
        db.query(TorneoSlot).filter(TorneoSlot.torneo_id == torneo_id).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "message": "Programación limpiada exitosamente",
            "slots_eliminados": slots_count,
            "partidos_desprogramados": partidos_desprogramados
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{torneo_id}/programar-partidos")
@router.post("/{torneo_id}/programar-automatico")  # Alias para compatibilidad con frontend
def programar_partidos_automatico(
    torneo_id: int,
    params: Optional[ProgramacionParams] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Programa automáticamente todos los partidos pendientes en los slots disponibles
    
    Considera:
    - Disponibilidad de slots
    - Bloqueos horarios de jugadores
    - Que una pareja no juegue dos partidos seguidos
    - Horarios diferentes para días de semana vs fin de semana
    
    Parámetros opcionales en body:
    - fecha_inicio: Fecha de inicio para crear slots
    - fecha_fin: Fecha de fin para crear slots
    - duracion_partido_minutos: Duración de cada partido (default: 70)
    - hora_inicio_semana/hora_fin_semana: Horarios Lun-Vie (default: 17:00-22:00)
    - hora_inicio_finde/hora_fin_finde: Horarios Sab-Dom (default: 09:00-21:00)
    """
    from ..models.torneo_models import TorneoSlot, TorneoCancha, TorneoBloqueoJugador, TorneoPareja
    from ..models.driveplus_models import Partido
    from ..services.torneo_zona_service import TorneoZonaService
    from datetime import datetime, timedelta
    
    # Extraer parámetros del body si existen
    fecha_inicio = params.fecha_inicio if params else None
    fecha_fin = params.fecha_fin if params else None
    duracion_minutos = params.duracion_partido_minutos if params else 70
    hora_inicio_semana = params.hora_inicio_semana if params else "17:00"
    hora_fin_semana = params.hora_fin_semana if params else "22:00"
    hora_inicio_finde = params.hora_inicio_finde if params else "09:00"
    hora_fin_finde = params.hora_fin_finde if params else "21:00"
    
    try:
        if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        # Si se proporcionan fechas, crear slots automáticamente
        if fecha_inicio and fecha_fin:
            canchas = db.query(TorneoCancha).filter(
                TorneoCancha.torneo_id == torneo_id,
                TorneoCancha.activa == True
            ).all()
            
            if not canchas:
                raise HTTPException(status_code=400, detail="No hay canchas configuradas. Crea canchas primero.")
            
            # Crear slots para cada día y cancha
            from datetime import datetime, time
            fecha_actual = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            fecha_final = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            
            # Parsear horarios configurados
            def parse_hora(hora_str):
                parts = hora_str.split(":")
                return time(int(parts[0]), int(parts[1]))
            
            h_inicio_semana = parse_hora(hora_inicio_semana)
            h_fin_semana = parse_hora(hora_fin_semana)
            h_inicio_finde = parse_hora(hora_inicio_finde)
            h_fin_finde = parse_hora(hora_fin_finde)
            
            # Detectar si cruza medianoche (hora fin es 00:00 o menor que inicio)
            # En ese caso, 00:00 significa medianoche del día siguiente
            cruza_medianoche_semana = h_fin_semana <= h_inicio_semana
            cruza_medianoche_finde = h_fin_finde <= h_inicio_finde
            
            # PRE-CARGAR slots existentes para evitar queries individuales
            slots_existentes = db.query(TorneoSlot).filter(
                TorneoSlot.torneo_id == torneo_id
            ).all()
            slots_existentes_set = {
                (s.cancha_id, s.fecha_hora_inicio) for s in slots_existentes
            }
            
            slots_creados = 0
            nuevos_slots = []
            while fecha_actual <= fecha_final:
                # Determinar si es fin de semana (5=Sábado, 6=Domingo)
                dia_semana = fecha_actual.weekday()
                es_finde = dia_semana >= 5
                
                # Seleccionar horarios según el día
                if es_finde:
                    hora_inicio_dia = h_inicio_finde
                    hora_fin_dia = h_fin_finde
                    cruza_medianoche = cruza_medianoche_finde
                else:
                    hora_inicio_dia = h_inicio_semana
                    hora_fin_dia = h_fin_semana
                    cruza_medianoche = cruza_medianoche_semana
                
                # Generar slots dinámicamente según duración del partido
                hora_actual = datetime.combine(fecha_actual, hora_inicio_dia)
                
                # Si cruza medianoche, el límite es al día siguiente
                if cruza_medianoche:
                    hora_limite = datetime.combine(fecha_actual + timedelta(days=1), hora_fin_dia)
                else:
                    hora_limite = datetime.combine(fecha_actual, hora_fin_dia)
                
                while hora_actual + timedelta(minutes=duracion_minutos) <= hora_limite:
                    for cancha in canchas:
                        inicio = hora_actual
                        fin = hora_actual + timedelta(minutes=duracion_minutos)
                        
                        # Verificar en memoria si ya existe
                        if (cancha.id, inicio) not in slots_existentes_set:
                            nuevo_slot = TorneoSlot(
                                torneo_id=torneo_id,
                                cancha_id=cancha.id,
                                fecha_hora_inicio=inicio,
                                fecha_hora_fin=fin,
                                ocupado=False
                            )
                            nuevos_slots.append(nuevo_slot)
                            slots_creados += 1
                    
                    # Avanzar al siguiente slot
                    hora_actual += timedelta(minutes=duracion_minutos)
                
                fecha_actual += timedelta(days=1)
            
            # Insertar todos los slots de una vez
            if nuevos_slots:
                for slot in nuevos_slots:
                    db.add(slot)
                db.flush()
        
        # Obtener partidos pendientes sin programar
        partidos = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.estado == 'pendiente',
            Partido.cancha_id == None
        ).all()
        
        if not partidos:
            return {"message": "No hay partidos pendientes para programar", "programados": 0, "sin_programar": 0, "partidos_sin_slot_detalle": []}
        
        # Obtener slots disponibles ordenados por fecha
        slots = db.query(TorneoSlot).filter(
            TorneoSlot.torneo_id == torneo_id,
            TorneoSlot.ocupado == False
        ).order_by(TorneoSlot.fecha_hora_inicio).all()
        
        if not slots:
            raise HTTPException(status_code=400, detail="No hay slots disponibles. Verifica que los horarios de inicio sean menores a los de fin.")
        
        # Obtener bloqueos de jugadores
        bloqueos = db.query(TorneoBloqueoJugador).filter(
            TorneoBloqueoJugador.torneo_id == torneo_id
        ).all()
        
        # Crear diccionario de bloqueos por jugador
        bloqueos_por_jugador = {}
        for b in bloqueos:
            if b.jugador_id not in bloqueos_por_jugador:
                bloqueos_por_jugador[b.jugador_id] = []
            bloqueos_por_jugador[b.jugador_id].append({
                "fecha": b.fecha,
                "hora_desde": b.hora_desde,
                "hora_hasta": b.hora_hasta
            })
        
        # PRE-CARGAR todas las parejas del torneo (optimización)
        todas_parejas = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == torneo_id
        ).all()
        parejas_dict = {p.id: p for p in todas_parejas}
        
        # PRE-CARGAR todos los perfiles de usuarios involucrados (optimización)
        from ..models.driveplus_models import PerfilUsuario
        jugadores_ids = set()
        for p in todas_parejas:
            jugadores_ids.add(p.jugador1_id)
            jugadores_ids.add(p.jugador2_id)
        
        perfiles = db.query(PerfilUsuario).filter(
            PerfilUsuario.id_usuario.in_(jugadores_ids)
        ).all()
        perfiles_dict = {p.id_usuario: p for p in perfiles}
        
        # Helper para obtener nombres de parejas (usa cache)
        def obtener_nombre_pareja(pareja):
            if not pareja:
                return "Pareja desconocida"
            perfil1 = perfiles_dict.get(pareja.jugador1_id)
            perfil2 = perfiles_dict.get(pareja.jugador2_id)
            nombre1 = f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Jugador {pareja.jugador1_id}"
            nombre2 = f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Jugador {pareja.jugador2_id}"
            return f"{nombre1} / {nombre2}"
        
        # Tracking de último partido por pareja (para evitar partidos seguidos)
        ultimo_partido_pareja = {}
        
        partidos_programados = 0
        partidos_no_programados = []
        
        # Contador de partidos de playoffs sin parejas definidas
        partidos_playoffs_pendientes = 0
        
        for partido in partidos:
            programado = False
            razon_no_programado = "Sin slots disponibles"
            
            # Verificar si es un partido de playoffs sin parejas definidas aún
            if partido.pareja1_id is None or partido.pareja2_id is None:
                # Es un partido de playoffs esperando clasificados
                partidos_playoffs_pendientes += 1
                continue  # No intentar programar, es normal
            
            # Obtener parejas del cache
            pareja1 = parejas_dict.get(partido.pareja1_id)
            pareja2 = parejas_dict.get(partido.pareja2_id)
            
            if not pareja1 or not pareja2:
                # Esto sería un error de datos (pareja_id existe pero no se encuentra)
                partidos_no_programados.append({
                    "partido_id": partido.id_partido,
                    "pareja1_nombre": obtener_nombre_pareja(pareja1) if pareja1 else f"Pareja #{partido.pareja1_id}",
                    "pareja2_nombre": obtener_nombre_pareja(pareja2) if pareja2 else f"Pareja #{partido.pareja2_id}",
                    "razon": "Error: pareja no encontrada en base de datos"
                })
                continue
            
            for slot in slots:
                if slot.ocupado:
                    continue
                
                # Verificar bloqueos de los 4 jugadores
                jugadores = [pareja1.jugador1_id, pareja1.jugador2_id, pareja2.jugador1_id, pareja2.jugador2_id]
                tiene_bloqueo = False
                jugador_bloqueado = None
                
                for jugador_id in jugadores:
                    if _jugador_tiene_bloqueo(bloqueos_por_jugador, jugador_id, slot):
                        tiene_bloqueo = True
                        jugador_bloqueado = jugador_id
                        break
                
                if tiene_bloqueo:
                    razon_no_programado = f"Bloqueo horario de jugador"
                    continue
                
                # Verificar que ninguna pareja jugó en el slot anterior
                slot_inicio = slot.fecha_hora_inicio
                pareja_sin_descanso = None
                for pareja_id in [partido.pareja1_id, partido.pareja2_id]:
                    if pareja_id in ultimo_partido_pareja:
                        ultimo_fin = ultimo_partido_pareja[pareja_id]
                        # Dar al menos 30 minutos de descanso
                        if slot_inicio < ultimo_fin + timedelta(minutes=30):
                            tiene_bloqueo = True
                            pareja_sin_descanso = pareja_id
                            break
                
                if tiene_bloqueo:
                    razon_no_programado = "Pareja necesita descanso entre partidos"
                    continue
                
                # Asignar slot al partido
                partido.cancha_id = slot.cancha_id
                partido.fecha_hora = slot.fecha_hora_inicio
                slot.ocupado = True
                slot.partido_id = partido.id_partido
                
                # Actualizar tracking
                ultimo_partido_pareja[partido.pareja1_id] = slot.fecha_hora_fin
                ultimo_partido_pareja[partido.pareja2_id] = slot.fecha_hora_fin
                
                partidos_programados += 1
                programado = True
                break
            
            if not programado:
                partidos_no_programados.append({
                    "partido_id": partido.id_partido,
                    "pareja1_nombre": obtener_nombre_pareja(pareja1),
                    "pareja2_nombre": obtener_nombre_pareja(pareja2),
                    "razon": razon_no_programado
                })
        
        db.commit()
        
        # Construir mensaje
        mensaje = f"Se programaron {partidos_programados} partidos"
        if partidos_playoffs_pendientes > 0:
            mensaje += f" ({partidos_playoffs_pendientes} partidos de playoffs esperan clasificados)"
        
        return {
            "message": mensaje,
            "programados": partidos_programados,
            "sin_programar": len(partidos_no_programados),
            "playoffs_pendientes": partidos_playoffs_pendientes,
            "partidos_sin_slot": [p["partido_id"] for p in partidos_no_programados[:10]],
            "partidos_sin_slot_detalle": partidos_no_programados[:10]
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _jugador_tiene_bloqueo(bloqueos_por_jugador, jugador_id, slot):
    """Verifica si un jugador tiene bloqueo en el horario del slot"""
    from datetime import datetime, time
    
    if jugador_id not in bloqueos_por_jugador:
        return False
    
    slot_fecha = slot.fecha_hora_inicio.date()
    slot_hora_inicio = slot.fecha_hora_inicio.time()
    slot_hora_fin = slot.fecha_hora_fin.time()
    
    for bloqueo in bloqueos_por_jugador[jugador_id]:
        if bloqueo["fecha"] != slot_fecha:
            continue
        
        # Parsear horas del bloqueo
        def parse_time(t):
            if isinstance(t, time):
                return t
            parts = t.split(":")
            return time(int(parts[0]), int(parts[1]))
        
        bloqueo_desde = parse_time(bloqueo["hora_desde"])
        bloqueo_hasta = parse_time(bloqueo["hora_hasta"])
        
        # Verificar solapamiento
        if not (slot_hora_fin <= bloqueo_desde or slot_hora_inicio >= bloqueo_hasta):
            return True
    
    return False


@router.post("/{torneo_id}/partidos/{partido_id}/reprogramar")
def reprogramar_partido(
    torneo_id: int,
    partido_id: int,
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Reprograma un partido a un slot específico
    """
    from ..models.torneo_models import TorneoSlot
    from ..models.driveplus_models import Partido
    from ..services.torneo_zona_service import TorneoZonaService
    
    try:
        if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        partido = db.query(Partido).filter(
            Partido.id_partido == partido_id,
            Partido.id_torneo == torneo_id
        ).first()
        
        if not partido:
            raise HTTPException(status_code=404, detail="Partido no encontrado")
        
        nuevo_slot = db.query(TorneoSlot).filter(
            TorneoSlot.id == slot_id,
            TorneoSlot.torneo_id == torneo_id
        ).first()
        
        if not nuevo_slot:
            raise HTTPException(status_code=404, detail="Slot no encontrado")
        
        if nuevo_slot.ocupado and nuevo_slot.partido_id != partido_id:
            raise HTTPException(status_code=400, detail="El slot ya está ocupado")
        
        # Liberar slot anterior si existe
        if partido.cancha_id:
            slot_anterior = db.query(TorneoSlot).filter(
                TorneoSlot.partido_id == partido_id
            ).first()
            if slot_anterior:
                slot_anterior.ocupado = False
                slot_anterior.partido_id = None
        
        # Asignar nuevo slot
        partido.cancha_id = nuevo_slot.cancha_id
        partido.fecha_hora = nuevo_slot.fecha_hora_inicio
        nuevo_slot.ocupado = True
        nuevo_slot.partido_id = partido_id
        
        db.commit()
        
        return {
            "message": "Partido reprogramado",
            "partido_id": partido_id,
            "nueva_fecha": nuevo_slot.fecha_hora_inicio.isoformat(),
            "cancha_id": nuevo_slot.cancha_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{torneo_id}/bloqueos")
def crear_bloqueo_jugador(
    torneo_id: int,
    jugador_id: int,
    fecha: str,
    hora_desde: str,
    hora_hasta: str,
    motivo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un bloqueo horario para un jugador
    
    Puede ser creado por el propio jugador o por un organizador
    """
    from ..models.torneo_models import TorneoBloqueoJugador, TorneoPareja
    from ..services.torneo_zona_service import TorneoZonaService
    from datetime import datetime
    
    try:
        # Verificar que el usuario es el jugador o es organizador
        es_organizador = TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario)
        es_jugador = current_user.id_usuario == jugador_id
        
        if not es_organizador and not es_jugador:
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        # Verificar que el jugador está inscrito en el torneo
        pareja = db.query(TorneoPareja).filter(
            TorneoPareja.torneo_id == torneo_id,
            (TorneoPareja.jugador1_id == jugador_id) | (TorneoPareja.jugador2_id == jugador_id)
        ).first()
        
        if not pareja:
            raise HTTPException(status_code=400, detail="El jugador no está inscrito en este torneo")
        
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        bloqueo = TorneoBloqueoJugador(
            torneo_id=torneo_id,
            jugador_id=jugador_id,
            fecha=fecha_dt,
            hora_desde=hora_desde,
            hora_hasta=hora_hasta,
            motivo=motivo
        )
        db.add(bloqueo)
        db.commit()
        db.refresh(bloqueo)
        
        return {
            "id": bloqueo.id,
            "jugador_id": bloqueo.jugador_id,
            "fecha": fecha,
            "hora_desde": hora_desde,
            "hora_hasta": hora_hasta,
            "motivo": motivo
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{torneo_id}/bloqueos")
def listar_bloqueos(
    torneo_id: int,
    jugador_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Lista bloqueos horarios del torneo"""
    from ..models.torneo_models import TorneoBloqueoJugador
    
    query = db.query(TorneoBloqueoJugador).filter(
        TorneoBloqueoJugador.torneo_id == torneo_id
    )
    
    if jugador_id:
        query = query.filter(TorneoBloqueoJugador.jugador_id == jugador_id)
    
    bloqueos = query.order_by(TorneoBloqueoJugador.fecha, TorneoBloqueoJugador.hora_desde).all()
    
    return [
        {
            "id": b.id,
            "jugador_id": b.jugador_id,
            "fecha": b.fecha.isoformat() if b.fecha else None,
            "hora_desde": b.hora_desde,
            "hora_hasta": b.hora_hasta,
            "motivo": b.motivo
        }
        for b in bloqueos
    ]


@router.delete("/{torneo_id}/bloqueos/{bloqueo_id}")
def eliminar_bloqueo(
    torneo_id: int,
    bloqueo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un bloqueo horario"""
    from ..models.torneo_models import TorneoBloqueoJugador
    from ..services.torneo_zona_service import TorneoZonaService
    
    bloqueo = db.query(TorneoBloqueoJugador).filter(
        TorneoBloqueoJugador.id == bloqueo_id,
        TorneoBloqueoJugador.torneo_id == torneo_id
    ).first()
    
    if not bloqueo:
        raise HTTPException(status_code=404, detail="Bloqueo no encontrado")
    
    # Verificar permisos
    es_organizador = TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario)
    es_jugador = current_user.id_usuario == bloqueo.jugador_id
    
    if not es_organizador and not es_jugador:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    db.delete(bloqueo)
    db.commit()
    
    return {"message": "Bloqueo eliminado"}


# ============================================
# CAMBIO MANUAL DE HORARIOS
# ============================================

class CambiarHorarioRequest(BaseModel):
    fecha: str  # "2026-02-06"
    hora: str   # "19:10"
    cancha_id: int


@router.put("/{torneo_id}/partidos/{partido_id}/cambiar-horario")
def cambiar_horario_partido(
    torneo_id: int,
    partido_id: int,
    request: CambiarHorarioRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cambia manualmente el horario y cancha de un partido
    Valida solapamientos con otros partidos en la misma cancha
    """
    from ..models.driveplus_models import Partido
    from ..models.torneo_models import TorneoCancha, TorneoPareja
    from ..services.torneo_zona_service import TorneoZonaService
    from datetime import datetime, timedelta
    
    try:
        # Verificar permisos
        if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
            raise HTTPException(status_code=403, detail="No tienes permisos")
        
        # Obtener partido
        partido = db.query(Partido).filter(
            Partido.id_partido == partido_id,
            Partido.id_torneo == torneo_id
        ).first()
        
        if not partido:
            raise HTTPException(status_code=404, detail="Partido no encontrado")
        
        # Verificar que la cancha existe y está activa
        cancha = db.query(TorneoCancha).filter(
            TorneoCancha.id == request.cancha_id,
            TorneoCancha.torneo_id == torneo_id,
            TorneoCancha.activa == True
        ).first()
        
        if not cancha:
            raise HTTPException(
                status_code=404, 
                detail="Cancha no encontrada o no está activa"
            )
        
        # Parsear fecha y hora
        try:
            fecha_hora_nueva = datetime.strptime(
                f"{request.fecha} {request.hora}:00",
                "%Y-%m-%d %H:%M:%S"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Formato de fecha/hora inválido: {str(e)}"
            )
        
        # Calcular fin del partido (50 minutos)
        fecha_hora_fin = fecha_hora_nueva + timedelta(minutes=50)
        
        # 🔍 VALIDAR SOLAPAMIENTO CON OTROS PARTIDOS EN LA MISMA CANCHA
        partidos_en_cancha = db.query(Partido).filter(
            Partido.id_torneo == torneo_id,
            Partido.cancha_id == request.cancha_id,
            Partido.id_partido != partido_id,  # Excluir el partido actual
            Partido.fecha_hora.isnot(None)
        ).all()
        
        conflictos = []
        for otro_partido in partidos_en_cancha:
            otro_inicio = otro_partido.fecha_hora
            
            # 🔴 FIX: Normalizar timezone - convertir ambas fechas a naive
            if otro_inicio.tzinfo is not None:
                otro_inicio = otro_inicio.replace(tzinfo=None)
            
            otro_fin = otro_inicio + timedelta(minutes=50)
            
            # Verificar solapamiento
            # Hay solapamiento si: nuevo_inicio < otro_fin AND nuevo_fin > otro_inicio
            if fecha_hora_nueva < otro_fin and fecha_hora_fin > otro_inicio:
                # Obtener nombres de parejas para el mensaje
                pareja1 = db.query(TorneoPareja).filter(
                    TorneoPareja.id == otro_partido.pareja1_id
                ).first()
                pareja2 = db.query(TorneoPareja).filter(
                    TorneoPareja.id == otro_partido.pareja2_id
                ).first()
                
                pareja1_nombre = "Pareja desconocida"
                pareja2_nombre = "Pareja desconocida"
                
                if pareja1:
                    j1 = db.query(Usuario).filter(Usuario.id_usuario == pareja1.jugador1_id).first()
                    j2 = db.query(Usuario).filter(Usuario.id_usuario == pareja1.jugador2_id).first()
                    if j1 and j2:
                        pareja1_nombre = f"{j1.nombre_usuario}/{j2.nombre_usuario}"
                
                if pareja2:
                    j1 = db.query(Usuario).filter(Usuario.id_usuario == pareja2.jugador1_id).first()
                    j2 = db.query(Usuario).filter(Usuario.id_usuario == pareja2.jugador2_id).first()
                    if j1 and j2:
                        pareja2_nombre = f"{j1.nombre_usuario}/{j2.nombre_usuario}"
                
                conflictos.append({
                    "partido_id": otro_partido.id_partido,
                    "pareja1": pareja1_nombre,
                    "pareja2": pareja2_nombre,
                    "fecha_hora": otro_inicio.strftime("%Y-%m-%d %H:%M"),
                    "cancha": cancha.nombre
                })
        
        # Si hay conflictos, retornar advertencia
        if conflictos:
            return {
                "success": False,
                "error": "SOLAPAMIENTO_DETECTADO",
                "message": f"El horario solicitado se solapa con {len(conflictos)} partido(s) en {cancha.nombre}",
                "conflictos": conflictos,
                "horario_solicitado": {
                    "fecha": request.fecha,
                    "hora": request.hora,
                    "cancha": cancha.nombre,
                    "inicio": fecha_hora_nueva.strftime("%Y-%m-%d %H:%M"),
                    "fin": fecha_hora_fin.strftime("%Y-%m-%d %H:%M")
                }
            }
        
        # ✅ No hay conflictos - Actualizar partido
        partido.fecha_hora = fecha_hora_nueva
        partido.fecha = fecha_hora_nueva  # También actualizar campo fecha
        partido.cancha_id = request.cancha_id
        
        db.commit()
        
        # Obtener nombres de parejas del partido actualizado
        pareja1 = db.query(TorneoPareja).filter(TorneoPareja.id == partido.pareja1_id).first()
        pareja2 = db.query(TorneoPareja).filter(TorneoPareja.id == partido.pareja2_id).first()
        
        pareja1_nombre = "Pareja desconocida"
        pareja2_nombre = "Pareja desconocida"
        
        if pareja1:
            j1 = db.query(Usuario).filter(Usuario.id_usuario == pareja1.jugador1_id).first()
            j2 = db.query(Usuario).filter(Usuario.id_usuario == pareja1.jugador2_id).first()
            if j1 and j2:
                pareja1_nombre = f"{j1.nombre_usuario}/{j2.nombre_usuario}"
        
        if pareja2:
            j1 = db.query(Usuario).filter(Usuario.id_usuario == pareja2.jugador1_id).first()
            j2 = db.query(Usuario).filter(Usuario.id_usuario == pareja2.jugador2_id).first()
            if j1 and j2:
                pareja2_nombre = f"{j1.nombre_usuario}/{j2.nombre_usuario}"
        
        return {
            "success": True,
            "message": "Horario actualizado correctamente",
            "partido": {
                "id": partido_id,
                "pareja1": pareja1_nombre,
                "pareja2": pareja2_nombre,
                "fecha": request.fecha,
                "hora": request.hora,
                "cancha": cancha.nombre,
                "cancha_id": cancha.id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
