from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List
from datetime import datetime

from ..database.config import get_db
from ..models.sala import Sala, SalaJugador
from ..models.driveplus_models import Usuario, PerfilUsuario, Partido, PartidoJugador, ResultadoPartido
from ..models.confirmacion import Confirmacion
from ..schemas.sala import SalaCreate, SalaResponse, SalaJoin, SalaCompleta
from ..auth.auth_utils import get_current_user
from ..utils.logger import Loggers

logger = Loggers.sala()

router = APIRouter(prefix="/salas", tags=["Salas"])

@router.post("/", response_model=SalaResponse)
async def crear_sala(
    sala_data: SalaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva sala de juego"""
    try:
        # Generar código único
        codigo = Sala.generar_codigo()
        
        # Verificar que el código sea único
        while db.query(Sala).filter(Sala.codigo_invitacion == codigo).first():
            codigo = Sala.generar_codigo()
        
        # Crear sala
        db_sala = Sala(
            nombre=sala_data.nombre,
            codigo_invitacion=codigo,
            fecha=sala_data.fecha,
            estado="esperando",
            id_creador=current_user.id_usuario,
            max_jugadores=sala_data.max_jugadores
        )
        
        db.add(db_sala)
        db.flush()
        
        # Agregar al creador como primer jugador
        db_jugador = SalaJugador(
            id_sala=db_sala.id_sala,
            id_usuario=current_user.id_usuario,
            orden=1
        )
        db.add(db_jugador)
        
        db.commit()
        db.refresh(db_sala)
        
        return SalaResponse(
            id_sala=str(db_sala.id_sala),
            nombre=db_sala.nombre,
            fecha=db_sala.fecha,
            estado=db_sala.estado,
            codigo_invitacion=db_sala.codigo_invitacion,
            id_creador=db_sala.id_creador,
            jugadores_actuales=1,
            max_jugadores=db_sala.max_jugadores,
            creado_en=db_sala.creado_en
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear sala: {str(e)}"
        )

@router.post("/unirse", response_model=SalaCompleta)
async def unirse_sala(
    join_data: SalaJoin,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unirse a una sala con código de invitación (OPTIMIZADO)"""
    
    try:
        # OPTIMIZACIÓN 1: Query única con joins para obtener toda la info necesaria
        sala_info = db.query(
            Sala.id_sala,
            Sala.codigo_invitacion,
            Sala.max_jugadores,
            Sala.estado,
            func.count(SalaJugador.id_usuario).label('jugadores_actuales'),
            func.sum(case((SalaJugador.id_usuario == current_user.id_usuario, 1), else_=0)).label('ya_esta')
        ).outerjoin(
            SalaJugador, Sala.id_sala == SalaJugador.id_sala
        ).filter(
            Sala.codigo_invitacion == join_data.codigo_invitacion.upper()
        ).group_by(
            Sala.id_sala, Sala.codigo_invitacion, Sala.max_jugadores, Sala.estado
        ).first()
        
        if not sala_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sala no encontrada"
            )
        
        # Verificaciones usando datos de la query única
        if sala_info.jugadores_actuales >= sala_info.max_jugadores:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La sala está llena"
            )
        
        if sala_info.ya_esta > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya estás en esta sala"
            )
        
        # OPTIMIZACIÓN 2: Agregar jugador con orden correcto
        db_jugador = SalaJugador(
            id_sala=sala_info.id_sala,
            id_usuario=current_user.id_usuario,
            orden=sala_info.jugadores_actuales + 1
        )
        db.add(db_jugador)
        db.commit()
        
        # OPTIMIZACIÓN 3: Notificar via WebSocket de forma asíncrona
        from ..websocket.connection_manager import manager
        try:
            await manager.broadcast_to_room(
                f"sala_{sala_info.id_sala}",
                {
                    "type": "jugador_unido",
                    "jugador": {
                        "id": str(current_user.id_usuario),
                        "nombre": current_user.nombre_usuario,
                        "rating": current_user.rating or 1500
                    }
                }
            )
        except Exception as ws_error:
            logger.warning(f"Error enviando WebSocket: {ws_error}")
        
        # OPTIMIZACIÓN 4: Retornar sala optimizada (reutilizar función optimizada)
        return await obtener_sala_optimizada(sala_info.id_sala, current_user, db)
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al unirse a sala: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al unirse a la sala: {str(e)}"
        )

@router.get("/{sala_id}", response_model=SalaCompleta)
async def obtener_sala(
    sala_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener información completa de una sala"""
    
    sala = db.query(Sala).filter(Sala.id_sala == sala_id).first()
    
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    # Obtener jugadores (batch: evitar N+1)
    jugadores_sala = db.query(SalaJugador).filter(
        SalaJugador.id_sala == sala_id
    ).order_by(SalaJugador.orden).all()
    
    jugadores = []
    if jugadores_sala:
        ids_usuario = [sj.id_usuario for sj in jugadores_sala]
        usuarios = db.query(Usuario).filter(Usuario.id_usuario.in_(ids_usuario)).all()
        perfiles = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario.in_(ids_usuario)).all()
        usuarios_dict = {u.id_usuario: u for u in usuarios}
        perfiles_dict = {p.id_usuario: p for p in perfiles}
        for sj in jugadores_sala:
            usuario = usuarios_dict.get(sj.id_usuario)
            perfil = perfiles_dict.get(sj.id_usuario)
            if usuario:
                jugadores.append({
                    "id_usuario": usuario.id_usuario,
                    "nombre_usuario": usuario.nombre_usuario,
                    "nombre": perfil.nombre if perfil else "",
                    "apellido": perfil.apellido if perfil else "",
                    "rating": usuario.rating,
                    "equipo": sj.equipo,
                    "orden": sj.orden
                })
    
    # Obtener resultado del partido si existe
    from ..models.driveplus_models import Partido, ResultadoPartido
    resultado = None
    estado_confirmacion = None
    
    if sala.id_partido:
        partido = db.query(Partido).filter(Partido.id_partido == sala.id_partido).first()
        if partido:
            estado_confirmacion = partido.estado_confirmacion
            
            # Buscar resultado en resultados_partidos (UNIFICADO)
            resultado_db = db.query(ResultadoPartido).filter(
                ResultadoPartido.id_partido == partido.id_partido
            ).first()
            
            if resultado_db:
                # Convertir a formato que espera el frontend
                resultado = {
                    "formato": "best_of_3",
                    "sets": [
                        {
                            "gamesEquipoA": set_data.get("juegos_eq1", 0),
                            "gamesEquipoB": set_data.get("juegos_eq2", 0),
                            "ganador": "equipoA" if set_data.get("juegos_eq1", 0) > set_data.get("juegos_eq2", 0) else "equipoB",
                            "completado": True
                        }
                        for set_data in resultado_db.detalle_sets
                    ],
                    "ganador": "equipoA" if partido.ganador_equipo == 1 else "equipoB",
                    "completado": True
                }
    
    return SalaCompleta(
        id_sala=str(sala.id_sala),
        nombre=sala.nombre,
        fecha=sala.fecha,
        estado=sala.estado,
        codigo_invitacion=sala.codigo_invitacion,
        id_creador=sala.id_creador,
        jugadores_actuales=len(jugadores),
        max_jugadores=sala.max_jugadores,
        creado_en=sala.creado_en,
        jugadores=jugadores,
        resultado=resultado,
        estado_confirmacion=estado_confirmacion
    )

@router.get("/", response_model=List[SalaCompleta])
async def listar_salas(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar todas las salas activas y las últimas 10 finalizadas donde el usuario participó (OPTIMIZADO)"""
    
    try:
        # OPTIMIZACIÓN 1: Query única con joins para salas activas
        salas_activas_query = db.query(Sala).filter(
            Sala.estado.in_(['esperando', 'activa', 'programada', 'en_juego'])
        ).order_by(Sala.creado_en.desc())
        
        # OPTIMIZACIÓN 2: Query única con joins para salas finalizadas del usuario
        salas_finalizadas_query = db.query(Sala).join(
            SalaJugador, Sala.id_sala == SalaJugador.id_sala
        ).filter(
            Sala.estado == 'finalizada',
            SalaJugador.id_usuario == current_user.id_usuario
        ).order_by(Sala.creado_en.desc()).limit(10)
        
        # Ejecutar ambas queries
        salas_activas = salas_activas_query.all()
        salas_finalizadas = salas_finalizadas_query.all()
        
        # Combinar y deduplicar
        salas_dict = {s.id_sala: s for s in salas_activas}
        for s in salas_finalizadas:
            if s.id_sala not in salas_dict:
                salas_dict[s.id_sala] = s
        
        salas = list(salas_dict.values())
        
    except Exception as e:
        logger.error(f"Error al obtener salas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener salas: {str(e)}"
        )
    
    if not salas:
        return []
    
    # OPTIMIZACIÓN 3: Batch query para todos los datos relacionados
    salas_ids = [s.id_sala for s in salas]
    partidos_ids = [s.id_partido for s in salas if s.id_partido]
    
    # Query 1: Todos los jugadores con usuarios y perfiles en una sola query
    jugadores_data = db.query(
        SalaJugador.id_sala,
        SalaJugador.id_usuario,
        SalaJugador.equipo,
        SalaJugador.orden,
        Usuario.nombre_usuario,
        Usuario.rating,
        PerfilUsuario.nombre,
        PerfilUsuario.apellido
    ).join(
        Usuario, SalaJugador.id_usuario == Usuario.id_usuario
    ).outerjoin(
        PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
    ).filter(
        SalaJugador.id_sala.in_(salas_ids)
    ).order_by(SalaJugador.id_sala, SalaJugador.orden).all()
    
    # Query 2: Todos los partidos relacionados
    partidos_data = {}
    if partidos_ids:
        partidos = db.query(Partido).filter(Partido.id_partido.in_(partidos_ids)).all()
        partidos_data = {p.id_partido: p for p in partidos}
    
    # Query 3: Todos los resultados de partidos
    resultados_data = {}
    if partidos_ids:
        resultados = db.query(ResultadoPartido).filter(
            ResultadoPartido.id_partido.in_(partidos_ids)
        ).all()
        resultados_data = {r.id_partido: r for r in resultados}
    
    # Query 4: Todos los cambios de ELO
    cambios_elo_data = {}
    if partidos_ids:
        cambios_elo = db.query(PartidoJugador).filter(
            PartidoJugador.id_partido.in_(partidos_ids)
        ).all()
        
        for cambio in cambios_elo:
            if cambio.id_partido not in cambios_elo_data:
                cambios_elo_data[cambio.id_partido] = []
            cambios_elo_data[cambio.id_partido].append({
                "id_usuario": cambio.id_usuario,
                "rating_antes": cambio.rating_antes,
                "rating_despues": cambio.rating_despues,
                "cambio_elo": cambio.cambio_elo
            })
    
    # Query 5: Todas las confirmaciones
    confirmaciones_data = {}
    if partidos_ids:
        confirmaciones = db.query(Confirmacion).filter(
            Confirmacion.id_partido.in_(partidos_ids),
            Confirmacion.tipo == 'confirmacion'
        ).all()
        
        for conf in confirmaciones:
            if conf.id_partido not in confirmaciones_data:
                confirmaciones_data[conf.id_partido] = []
            confirmaciones_data[conf.id_partido].append(conf.id_usuario)
    
    # OPTIMIZACIÓN 4: Procesar datos en memoria (mucho más rápido que queries)
    jugadores_por_sala = {}
    for row in jugadores_data:
        id_sala = row.id_sala
        if id_sala not in jugadores_por_sala:
            jugadores_por_sala[id_sala] = []
        
        # Construir nombre completo
        nombre_completo = f"{row.nombre} {row.apellido}".strip() if row.nombre else row.nombre_usuario
        
        jugadores_por_sala[id_sala].append({
            "id": str(row.id_usuario),
            "nombre": nombre_completo,
            "nombre_usuario": row.nombre_usuario,
            "rating": row.rating or 1500,
            "equipo": row.equipo,
            "esCreador": False  # Se actualizará después
        })
    
    
    # OPTIMIZACIÓN 5: Construir resultado final (procesamiento en memoria)
    resultado = []
    for sala in salas:
        try:
            jugadores = jugadores_por_sala.get(sala.id_sala, [])
            
            # Marcar al creador
            for jugador in jugadores:
                if int(jugador["id"]) == sala.id_creador:
                    jugador["esCreador"] = True
            
            # Obtener datos del partido si existe (usando datos pre-cargados)
            resultado_partido = None
            estado_confirmacion = None
            cambios_elo = None
            elo_aplicado = False
            usuarios_confirmados = []
            
            if sala.id_partido:
                # Usar datos pre-cargados (no más queries)
                partido = partidos_data.get(sala.id_partido)
                if partido:
                    estado_confirmacion = partido.estado_confirmacion
                    elo_aplicado = getattr(partido, 'elo_aplicado', False)
                
                # Resultado del partido
                resultado_db = resultados_data.get(sala.id_partido)
                if resultado_db:
                    resultado_partido = {
                        "formato": "best_of_3",
                        "sets": [
                            {
                                "gamesEquipoA": set_data.get("juegos_eq1", 0),
                                "gamesEquipoB": set_data.get("juegos_eq2", 0),
                                "ganador": "equipoA" if set_data.get("juegos_eq1", 0) > set_data.get("juegos_eq2", 0) else "equipoB",
                                "completado": True
                            }
                            for set_data in resultado_db.detalle_sets
                        ],
                        "ganador": "equipoA" if partido and partido.ganador_equipo == 1 else "equipoB",
                        "completado": True
                    }
                
                # Cambios de ELO
                cambios_elo = cambios_elo_data.get(sala.id_partido)
                
                # Usuarios confirmados
                usuarios_confirmados = confirmaciones_data.get(sala.id_partido, [])
            
            sala_completa = SalaCompleta(
                id_sala=str(sala.id_sala),
                nombre=sala.nombre,
                fecha=sala.fecha,
                estado=sala.estado,
                codigo_invitacion=sala.codigo_invitacion,
                id_creador=sala.id_creador,
                jugadores_actuales=len(jugadores),
                max_jugadores=sala.max_jugadores,
                creado_en=sala.creado_en,
                jugadores=jugadores,
                resultado=resultado_partido,
                estado_confirmacion=estado_confirmacion,
                cambios_elo=cambios_elo,
                elo_aplicado=elo_aplicado,
                usuarios_confirmados=usuarios_confirmados
            )
            resultado.append(sala_completa)
            
        except Exception as e:
            logger.error(f"Error al procesar sala {sala.id_sala}: {str(e)}")
            continue
    
    return resultado

@router.post("/{sala_id}/asignar-equipos")
async def asignar_equipos(
    sala_id: int,
    equipos: dict,  # {"jugador_id": equipo_numero}
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Asignar equipos a los jugadores (solo creador)"""
    
    sala = db.query(Sala).filter(Sala.id_sala == sala_id).first()
    
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    if sala.id_creador != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el creador puede asignar equipos"
        )
    
    try:
        # Actualizar equipos
        for jugador_id, equipo in equipos.items():
            db.query(SalaJugador).filter(
                SalaJugador.id_sala == sala_id,
                SalaJugador.id_usuario == int(jugador_id)
            ).update({"equipo": equipo})
        
        db.commit()
        
        return {"message": "Equipos asignados correctamente"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al asignar equipos: {str(e)}"
        )

@router.post("/{sala_id}/iniciar")
async def iniciar_partido(
    sala_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Iniciar el partido (solo creador, cuando haya 4 jugadores)"""
    
    sala = db.query(Sala).filter(Sala.id_sala == sala_id).first()
    
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    if sala.id_creador != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el creador puede iniciar el partido"
        )
    
    # Verificar que haya 4 jugadores
    jugadores = db.query(SalaJugador).filter(
        SalaJugador.id_sala == sala_id
    ).all()
    
    if len(jugadores) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Se necesitan 4 jugadores. Actualmente hay {len(jugadores)}"
        )
    
    # Verificar que todos tengan equipo asignado
    sin_equipo = [j for j in jugadores if j.equipo is None]
    if sin_equipo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todos los jugadores deben tener un equipo asignado"
        )
    
    # VERIFICAR ANTI-TRAMPA
    from ..services.anti_trampa_service import AntiTrampaService
    
    jugadores_ids = [j.id_usuario for j in jugadores]
    verificacion = AntiTrampaService.verificar_limite_partidos(jugadores_ids, db)
    
    if not verificacion["puede_jugar"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "limite_partidos_excedido",
                "mensaje": verificacion["mensaje"],
                "detalles": {
                    "jugadores_bloqueados": verificacion["jugadores_bloqueados"],
                    "partidos_jugados": verificacion["partidos_jugados"],
                    "limite": verificacion["limite"],
                    "proxima_disponibilidad": verificacion["proxima_disponibilidad"].isoformat() if verificacion["proxima_disponibilidad"] else None
                }
            }
        )
    
    try:
        # Crear el partido en la tabla de partidos
        from ..models.driveplus_models import Partido, PartidoJugador
        
        db_partido = Partido(
            fecha=sala.fecha if sala.fecha else datetime.now(),
            estado="pendiente",
            id_creador=current_user.id_usuario,
            tipo="amistoso",
            id_sala=sala_id,
            creado_por=current_user.id_usuario,
            estado_confirmacion="sin_resultado"
        )
        db.add(db_partido)
        db.flush()
        
        # Agregar jugadores al partido
        for jugador in jugadores:
            db_partido_jugador = PartidoJugador(
                id_partido=db_partido.id_partido,
                id_usuario=jugador.id_usuario,
                equipo=jugador.equipo
            )
            db.add(db_partido_jugador)
        
        # Registrar en historial de enfrentamientos
        AntiTrampaService.registrar_enfrentamiento(
            id_partido=db_partido.id_partido,
            jugadores_ids=jugadores_ids,
            tipo_partido="amistoso",
            db=db
        )
        
        # Actualizar sala
        sala.estado = "en_juego"
        sala.id_partido = db_partido.id_partido
        
        db.commit()
        
        return {
            "message": "Partido iniciado",
            "id_partido": db_partido.id_partido
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar partido: {str(e)}"
        )


# ============================================
# ENDPOINTS DE RESULTADOS Y CONFIRMACIONES
# ============================================

@router.post("/{sala_id}/resultado")
async def cargar_resultado(
    sala_id: int,
    resultado_data: dict,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cargar resultado del partido (solo creador) - UNIFICADO"""
    from ..schemas.resultado_padel import ResultadoPadelSchema
    from ..models.driveplus_models import Partido, ResultadoPartido
    
    sala = db.query(Sala).filter(Sala.id_sala == sala_id).first()
    
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    if sala.id_creador != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el creador puede cargar el resultado"
        )
    
    if not sala.id_partido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El partido no ha sido iniciado"
        )
    
    # Validar resultado con Pydantic
    try:
        resultado = ResultadoPadelSchema(**resultado_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resultado inválido: {str(e)}"
        )
    
    try:
        # VALIDACIONES ROBUSTAS
        from ..utils.padel_validator import PadelValidator
        
        # Convertir formato del marcador a formato para validación
        sets_para_validar = []
        for set_info in resultado.sets:
            sets_para_validar.append({
                'juegos_eq1': set_info.gamesEquipoA,
                'juegos_eq2': set_info.gamesEquipoB,
                'esSuperTiebreak': getattr(set_info, 'esSuperTiebreak', False)
            })
        
        # Preparar supertiebreak si existe (formato antiguo)
        supertiebreak_para_validar = None
        if resultado.supertiebreak and resultado.supertiebreak.completado:
            supertiebreak_para_validar = {
                'puntos_eq1': resultado.supertiebreak.puntosEquipoA,
                'puntos_eq2': resultado.supertiebreak.puntosEquipoB
            }
        
        # Validar resultado completo
        es_valido, errores = PadelValidator.validar_resultado_completo(
            sets_para_validar, 
            supertiebreak_para_validar
        )
        
        if not es_valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resultado inválido: {'; '.join(errores)}"
            )
        
        # Validar que sea razonable (detectar posibles trampas)
        es_razonable, advertencias = PadelValidator.validar_resultado_razonable(sets_para_validar)
        if not es_razonable:
            # Log advertencias pero no bloquear
            print(f"⚠️ Advertencias en resultado: {'; '.join(advertencias)}")
        
        # Obtener partido
        partido = db.query(Partido).filter(Partido.id_partido == sala.id_partido).first()
        
        if not partido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partido no encontrado"
            )
        
        # Verificar si ya existe resultado
        resultado_existente = db.query(ResultadoPartido).filter(
            ResultadoPartido.id_partido == partido.id_partido
        ).first()
        
        # Si ya existe y está confirmado, no permitir edición
        if resultado_existente and resultado_existente.confirmado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El resultado ya fue confirmado y no se puede editar"
            )
        
        # Verificar si ya hay confirmaciones de otros jugadores
        from ..models.confirmacion import Confirmacion
        confirmaciones_existentes = db.query(Confirmacion).filter(
            Confirmacion.id_partido == partido.id_partido,
            Confirmacion.tipo == 'confirmacion'
        ).count()
        
        if confirmaciones_existentes > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede modificar el resultado: {confirmaciones_existentes} jugador(es) ya confirmaron"
            )
        
        # Si existe pero no está confirmado y no hay confirmaciones, permitir actualización
        if resultado_existente and not resultado_existente.confirmado:
            db.delete(resultado_existente)
            db.flush()
        
        # Convertir formato del marcador a formato unificado
        sets_data = resultado.sets
        sets_eq1 = 0
        sets_eq2 = 0
        detalle_sets = []
        
        for idx, set_info in enumerate(sets_data, 1):
            games_eq1 = set_info.gamesEquipoA
            games_eq2 = set_info.gamesEquipoB
            
            # Contar sets ganados
            if games_eq1 > games_eq2:
                sets_eq1 += 1
            elif games_eq2 > games_eq1:
                sets_eq2 += 1
            
            # Formato unificado
            detalle_set = {
                "set": idx,
                "juegos_eq1": games_eq1,
                "juegos_eq2": games_eq2
            }
            
            # Agregar tiebreak si existe
            if hasattr(set_info, 'tiebreakEquipoA') and set_info.tiebreakEquipoA is not None:
                detalle_set["tiebreak_eq1"] = set_info.tiebreakEquipoA
                detalle_set["tiebreak_eq2"] = set_info.tiebreakEquipoB
            
            detalle_sets.append(detalle_set)
        
        # Crear entrada en resultados_partidos
        nuevo_resultado = ResultadoPartido(
            id_partido=partido.id_partido,
            id_reportador=current_user.id_usuario,
            sets_eq1=sets_eq1,
            sets_eq2=sets_eq2,
            detalle_sets=detalle_sets,
            confirmado=False,
            desenlace="normal"
        )
        
        db.add(nuevo_resultado)
        
        # Actualizar partido
        partido.ganador_equipo = 1 if resultado.ganador == "equipoA" else 2
        partido.estado_confirmacion = "pendiente_confirmacion"
        partido.estado = "pendiente"
        
        db.commit()
        db.refresh(nuevo_resultado)
        
        return {
            "success": True,
            "mensaje": "Resultado guardado. Esperando confirmación de rivales.",
            "partido": {
                "id_partido": partido.id_partido,
                "resultado": {
                    "sets_eq1": sets_eq1,
                    "sets_eq2": sets_eq2,
                    "detalle_sets": detalle_sets
                },
                "estado_confirmacion": partido.estado_confirmacion
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar resultado: {str(e)}"
        )


@router.get("/{sala_id}/resultado")
async def obtener_resultado(
    sala_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener resultado del partido"""
    from ..models.driveplus_models import Partido
    from ..services.confirmacion_service import ConfirmacionService
    
    sala = db.query(Sala).filter(Sala.id_sala == sala_id).first()
    
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    if not sala.id_partido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El partido no ha sido iniciado"
        )
    
    partido = db.query(Partido).filter(Partido.id_partido == sala.id_partido).first()
    
    if not partido or not partido.resultado_padel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay resultado cargado"
        )
    
    # Obtener estado de confirmaciones
    estado_confirmaciones = ConfirmacionService.obtener_estado_confirmaciones(
        partido.id_partido,
        current_user.id_usuario,
        db
    )
    
    return {
        "id_partido": partido.id_partido,
        "resultado": partido.resultado_padel,
        "ganador_equipo": partido.ganador_equipo,
        "estado_confirmacion": partido.estado_confirmacion,
        "elo_aplicado": partido.elo_aplicado,
        "estado_confirmaciones": estado_confirmaciones
    }


@router.post("/{sala_id}/confirmar")
async def confirmar_resultado(
    sala_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirmar resultado del partido (rivales)"""
    from ..services.confirmacion_service import ConfirmacionService
    
    sala = db.query(Sala).filter(Sala.id_sala == sala_id).first()
    
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    if not sala.id_partido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El partido no ha sido iniciado"
        )
    
    try:
        resultado = ConfirmacionService.confirmar_resultado(
            sala.id_partido,
            current_user.id_usuario,
            db
        )
        
        # Si el Elo fue aplicado (todos confirmaron), finalizar la sala
        if resultado.get('elo_aplicado'):
            sala.estado = 'finalizada'
            db.commit()
        
        return resultado
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar resultado: {str(e)}"
        )


@router.post("/{sala_id}/reportar")
async def reportar_resultado(
    sala_id: int,
    reporte_data: dict,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reportar resultado como incorrecto"""
    from ..services.confirmacion_service import ConfirmacionService
    
    sala = db.query(Sala).filter(Sala.id_sala == sala_id).first()
    
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    if not sala.id_partido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El partido no ha sido iniciado"
        )
    
    motivo = reporte_data.get("motivo")
    if not motivo or len(motivo) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El motivo debe tener al menos 10 caracteres"
        )
    
    try:
        resultado = ConfirmacionService.reportar_resultado(
            sala.id_partido,
            current_user.id_usuario,
            motivo,
            db
        )
        
        return resultado
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reportar resultado: {str(e)}"
        )


@router.get("/confirmaciones-pendientes")
async def obtener_confirmaciones_pendientes(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener salas con confirmaciones pendientes del usuario"""
    from ..models.driveplus_models import Partido, PartidoJugador
    from sqlalchemy import and_
    
    # Buscar partidos donde el usuario participa y están pendientes de confirmación
    partidos_usuario = db.query(PartidoJugador).filter(
        PartidoJugador.id_usuario == current_user.id_usuario
    ).all()
    
    partidos_ids = [p.id_partido for p in partidos_usuario]
    
    # Filtrar solo los que están pendientes de confirmación
    partidos_pendientes = db.query(Partido).filter(
        and_(
            Partido.id_partido.in_(partidos_ids),
            Partido.estado_confirmacion == "pendiente_confirmacion",
            Partido.creado_por != current_user.id_usuario  # No incluir los que creó el usuario
        )
    ).all()
    
    if not partidos_pendientes:
        return {"pendientes": [], "total": 0}
    
    partidos_ids_pend = [p.id_partido for p in partidos_pendientes]
    partidos_dict = {p.id_partido: p for p in partidos_pendientes}
    
    # Batch: salas por id_partido y confirmaciones del usuario
    salas = db.query(Sala).filter(Sala.id_partido.in_(partidos_ids_pend)).all()
    salas_por_partido = {s.id_partido: s for s in salas}
    confirmaciones = db.query(Confirmacion.id_partido).filter(
        Confirmacion.id_partido.in_(partidos_ids_pend),
        Confirmacion.id_usuario == current_user.id_usuario
    ).all()
    partidos_ya_confirmados = {c.id_partido for c in confirmaciones}
    
    resultado = []
    for partido_id in partidos_ids_pend:
        partido = partidos_dict.get(partido_id)
        sala = salas_por_partido.get(partido_id)
        if sala and partido_id not in partidos_ya_confirmados:
            resultado.append({
                "id_sala": sala.id_sala,
                "nombre": sala.nombre,
                "fecha": sala.fecha,
                "id_partido": partido.id_partido,
                "resultado": partido.resultado_padel,
                "ganador_equipo": partido.ganador_equipo
            })
    
    return {
        "pendientes": resultado,
        "total": len(resultado)
    }


@router.delete("/{id_sala}")
async def eliminar_sala(
    id_sala: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar una sala
    Solo el creador puede eliminar la sala
    Si la sala tiene un partido asociado, también se elimina del historial anti-trampa
    """
    try:
        # Buscar la sala
        sala = db.query(Sala).filter(Sala.id_sala == id_sala).first()
        
        if not sala:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sala no encontrada"
            )
        
        # Verificar que el usuario sea el creador
        if sala.id_creador != current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el creador puede eliminar la sala"
            )
        
        # Eliminar registros del historial anti-trampa si existen
        # Buscar partidos asociados a esta sala y eliminar su historial
        from ..models.driveplus_models import Partido
        from ..models.historial_enfrentamiento import HistorialEnfrentamiento
        partidos_sala = db.query(Partido).filter(Partido.id_sala == id_sala).all()
        for partido in partidos_sala:
            db.query(HistorialEnfrentamiento).filter(
                HistorialEnfrentamiento.id_partido == partido.id_partido
            ).delete()
        
        # Eliminar jugadores de la sala
        db.query(SalaJugador).filter(
            SalaJugador.id_sala == id_sala
        ).delete()
        
        # Eliminar la sala
        db.delete(sala)
        db.commit()
        
        return {
            "message": "Sala eliminada exitosamente",
            "id_sala": id_sala
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar sala: {str(e)}"
        )

# ============================================
# FUNCIONES AUXILIARES OPTIMIZADAS
# ============================================

async def obtener_sala_optimizada(
    sala_id: int,
    current_user: Usuario,
    db: Session
) -> SalaCompleta:
    """Obtener información completa de una sala de forma optimizada"""
    
    # Query única para obtener sala con jugadores
    sala_data = db.query(
        Sala.id_sala,
        Sala.nombre,
        Sala.fecha,
        Sala.estado,
        Sala.codigo_invitacion,
        Sala.id_creador,
        Sala.max_jugadores,
        Sala.creado_en,
        Sala.id_partido
    ).filter(Sala.id_sala == sala_id).first()
    
    if not sala_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    # Query optimizada para jugadores
    jugadores_data = db.query(
        SalaJugador.id_usuario,
        SalaJugador.equipo,
        SalaJugador.orden,
        Usuario.nombre_usuario,
        Usuario.rating,
        PerfilUsuario.nombre,
        PerfilUsuario.apellido
    ).join(
        Usuario, SalaJugador.id_usuario == Usuario.id_usuario
    ).outerjoin(
        PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
    ).filter(
        SalaJugador.id_sala == sala_id
    ).order_by(SalaJugador.orden).all()
    
    # Procesar jugadores
    jugadores = []
    for row in jugadores_data:
        nombre_completo = f"{row.nombre} {row.apellido}".strip() if row.nombre else row.nombre_usuario
        jugadores.append({
            "id": str(row.id_usuario),
            "nombre": nombre_completo,
            "nombre_usuario": row.nombre_usuario,
            "rating": row.rating or 1500,
            "equipo": row.equipo,
            "esCreador": row.id_usuario == sala_data.id_creador
        })
    
    # Datos del partido (si existe)
    resultado_partido = None
    estado_confirmacion = None
    cambios_elo = None
    elo_aplicado = False
    usuarios_confirmados = []
    
    if sala_data.id_partido:
        from ..models.driveplus_models import Partido, ResultadoPartido, PartidoJugador
        from ..models.confirmacion import Confirmacion
        
        # Obtener datos del partido
        partido = db.query(Partido).filter(Partido.id_partido == sala_data.id_partido).first()
        if partido:
            estado_confirmacion = partido.estado_confirmacion
            elo_aplicado = getattr(partido, 'elo_aplicado', False)
            
            # Resultado
            resultado_db = db.query(ResultadoPartido).filter(
                ResultadoPartido.id_partido == sala_data.id_partido
            ).first()
            
            if resultado_db:
                resultado_partido = {
                    "formato": "best_of_3",
                    "sets": [
                        {
                            "gamesEquipoA": set_data.get("juegos_eq1", 0),
                            "gamesEquipoB": set_data.get("juegos_eq2", 0),
                            "ganador": "equipoA" if set_data.get("juegos_eq1", 0) > set_data.get("juegos_eq2", 0) else "equipoB",
                            "completado": True
                        }
                        for set_data in resultado_db.detalle_sets
                    ],
                    "ganador": "equipoA" if partido.ganador_equipo == 1 else "equipoB",
                    "completado": True
                }
            
            # Cambios ELO
            cambios_elo_db = db.query(PartidoJugador).filter(
                PartidoJugador.id_partido == sala_data.id_partido
            ).all()
            
            if cambios_elo_db:
                cambios_elo = [
                    {
                        "id_usuario": cambio.id_usuario,
                        "rating_antes": cambio.rating_antes,
                        "rating_despues": cambio.rating_despues,
                        "cambio_elo": cambio.cambio_elo
                    }
                    for cambio in cambios_elo_db
                ]
            
            # Confirmaciones
            confirmaciones = db.query(Confirmacion).filter(
                Confirmacion.id_partido == sala_data.id_partido,
                Confirmacion.tipo == 'confirmacion'
            ).all()
            usuarios_confirmados = [conf.id_usuario for conf in confirmaciones]
    
    return SalaCompleta(
        id_sala=str(sala_data.id_sala),
        nombre=sala_data.nombre,
        fecha=sala_data.fecha,
        estado=sala_data.estado,
        codigo_invitacion=sala_data.codigo_invitacion,
        id_creador=sala_data.id_creador,
        jugadores_actuales=len(jugadores),
        max_jugadores=sala_data.max_jugadores,
        creado_en=sala_data.creado_en,
        jugadores=jugadores,
        resultado=resultado_partido,
        estado_confirmacion=estado_confirmacion,
        cambios_elo=cambios_elo,
        elo_aplicado=elo_aplicado,
        usuarios_confirmados=usuarios_confirmados
    )