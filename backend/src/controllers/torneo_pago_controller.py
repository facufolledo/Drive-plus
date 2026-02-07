"""
Controller para gestión de pagos y cambios de compañero en torneos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database.config import get_db
from ..models.torneo_models import Torneo, TorneoPareja, TorneoPagoHistorial
from ..models.driveplus_models import Usuario
from ..schemas.pago_schemas import (
    SubirComprobanteRequest,
    VerificarPagoRequest,
    CambiarCompaneroRequest,
    ActualizarDisponibilidadRequest,
    DatosPagoResponse,
    EstadoPagoResponse
)
from ..auth.auth_utils import get_current_user
from ..services.torneo_zona_service import TorneoZonaService

router = APIRouter(prefix="/torneos", tags=["Torneos - Pagos"])


# ============================================
# ENDPOINTS DE INFORMACIÓN DE PAGO
# ============================================

@router.get("/{torneo_id}/datos-pago", response_model=DatosPagoResponse)
async def obtener_datos_pago(
    torneo_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los datos de pago del torneo (alias, monto, etc.)
    Público para que los jugadores puedan ver antes de inscribirse
    """
    torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
    if not torneo:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    
    return DatosPagoResponse(
        requiere_pago=torneo.requiere_pago or False,
        monto_inscripcion=float(torneo.monto_inscripcion) if torneo.monto_inscripcion else None,
        alias_cbu_cvu=torneo.alias_cbu_cvu,
        titular_cuenta=torneo.titular_cuenta,
        banco=torneo.banco
    )


@router.get("/{torneo_id}/parejas/{pareja_id}/estado-pago", response_model=EstadoPagoResponse)
async def obtener_estado_pago(
    torneo_id: int,
    pareja_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el estado de pago de una pareja
    Solo accesible por los jugadores de la pareja o el organizador
    """
    pareja = db.query(TorneoPareja).filter(
        TorneoPareja.id == pareja_id,
        TorneoPareja.torneo_id == torneo_id
    ).first()
    
    if not pareja:
        raise HTTPException(status_code=404, detail="Pareja no encontrada")
    
    # Verificar permisos
    es_organizador = TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario)
    es_jugador = pareja.jugador1_id == current_user.id_usuario or pareja.jugador2_id == current_user.id_usuario
    
    if not (es_organizador or es_jugador):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver este pago")
    
    return EstadoPagoResponse(
        pareja_id=pareja.id,
        pago_estado=pareja.pago_estado or 'pendiente',
        pago_monto=float(pareja.pago_monto) if pareja.pago_monto else None,
        pago_comprobante_url=pareja.pago_comprobante_url,
        pago_fecha_acreditacion=pareja.pago_fecha_acreditacion.isoformat() if pareja.pago_fecha_acreditacion else None,
        motivo_rechazo_pago=pareja.motivo_rechazo_pago
    )


# ============================================
# ENDPOINTS DE GESTIÓN DE PAGO (JUGADORES)
# ============================================

@router.post("/{torneo_id}/parejas/{pareja_id}/subir-comprobante")
async def subir_comprobante_pago(
    torneo_id: int,
    pareja_id: int,
    data: SubirComprobanteRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Sube el comprobante de pago de una pareja
    Solo accesible por los jugadores de la pareja
    """
    pareja = db.query(TorneoPareja).filter(
        TorneoPareja.id == pareja_id,
        TorneoPareja.torneo_id == torneo_id
    ).first()
    
    if not pareja:
        raise HTTPException(status_code=404, detail="Pareja no encontrada")
    
    # Verificar que sea uno de los jugadores
    if pareja.jugador1_id != current_user.id_usuario and pareja.jugador2_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Solo los jugadores de la pareja pueden subir el comprobante")
    
    # Verificar que la pareja esté confirmada
    if pareja.estado != 'confirmada':
        raise HTTPException(status_code=400, detail="La pareja debe estar confirmada antes de subir el comprobante")
    
    # Registrar en historial
    historial = TorneoPagoHistorial(
        pareja_id=pareja.id,
        estado_anterior=pareja.pago_estado,
        estado_nuevo='pagado',
        monto=pareja.pago_monto,
        comprobante_url=data.comprobante_url,
        observaciones="Comprobante subido por jugador",
        modificado_por=current_user.id_usuario
    )
    db.add(historial)
    
    # Actualizar pareja
    pareja.pago_comprobante_url = data.comprobante_url
    pareja.pago_estado = 'pagado'
    pareja.motivo_rechazo_pago = None  # Limpiar rechazo anterior si existía
    
    db.commit()
    db.refresh(pareja)
    
    return {
        "mensaje": "Comprobante subido exitosamente. Pendiente de verificación por el organizador.",
        "pago_estado": pareja.pago_estado
    }


# ============================================
# ENDPOINTS DE VERIFICACIÓN DE PAGO (ORGANIZADOR)
# ============================================

@router.patch("/{torneo_id}/parejas/{pareja_id}/verificar-pago")
async def verificar_pago(
    torneo_id: int,
    pareja_id: int,
    data: VerificarPagoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Verifica o rechaza el pago de una pareja
    Solo accesible por organizadores del torneo
    """
    # Verificar que sea organizador
    if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
        raise HTTPException(status_code=403, detail="Solo los organizadores pueden verificar pagos")
    
    pareja = db.query(TorneoPareja).filter(
        TorneoPareja.id == pareja_id,
        TorneoPareja.torneo_id == torneo_id
    ).first()
    
    if not pareja:
        raise HTTPException(status_code=404, detail="Pareja no encontrada")
    
    if pareja.pago_estado != 'pagado':
        raise HTTPException(status_code=400, detail="La pareja debe tener un pago pendiente de verificación")
    
    estado_anterior = pareja.pago_estado
    
    if data.aprobado:
        # Aprobar pago
        pareja.pago_estado = 'verificado'
        pareja.pago_fecha_acreditacion = datetime.now()
        pareja.pago_verificado_por = current_user.id_usuario
        pareja.motivo_rechazo_pago = None
        mensaje = "Pago verificado exitosamente"
    else:
        # Rechazar pago
        if not data.motivo_rechazo:
            raise HTTPException(status_code=400, detail="Debe proporcionar un motivo de rechazo")
        
        pareja.pago_estado = 'rechazado'
        pareja.motivo_rechazo_pago = data.motivo_rechazo
        mensaje = "Pago rechazado"
    
    # Registrar en historial
    historial = TorneoPagoHistorial(
        pareja_id=pareja.id,
        estado_anterior=estado_anterior,
        estado_nuevo=pareja.pago_estado,
        monto=pareja.pago_monto,
        comprobante_url=pareja.pago_comprobante_url,
        observaciones=data.motivo_rechazo if not data.aprobado else "Pago verificado",
        modificado_por=current_user.id_usuario
    )
    db.add(historial)
    
    db.commit()
    db.refresh(pareja)
    
    return {
        "mensaje": mensaje,
        "pago_estado": pareja.pago_estado,
        "motivo_rechazo": pareja.motivo_rechazo_pago
    }


@router.get("/{torneo_id}/pagos-pendientes")
async def listar_pagos_pendientes(
    torneo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todas las parejas con pagos pendientes de verificación
    Solo accesible por organizadores
    """
    if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
        raise HTTPException(status_code=403, detail="Solo los organizadores pueden ver los pagos pendientes")
    
    from ..models.driveplus_models import PerfilUsuario
    
    parejas = db.query(TorneoPareja).filter(
        TorneoPareja.torneo_id == torneo_id,
        TorneoPareja.pago_estado == 'pagado'
    ).all()
    
    if not parejas:
        return {"total": 0, "parejas": []}
    
    # Batch perfiles (evitar N+1)
    jugador_ids = set()
    for p in parejas:
        jugador_ids.add(p.jugador1_id)
        jugador_ids.add(p.jugador2_id)
    perfiles = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario.in_(jugador_ids)).all()
    perfiles_dict = {pr.id_usuario: pr for pr in perfiles}
    
    resultado = []
    for pareja in parejas:
        perfil1 = perfiles_dict.get(pareja.jugador1_id)
        perfil2 = perfiles_dict.get(pareja.jugador2_id)
        resultado.append({
            "pareja_id": pareja.id,
            "jugador1_nombre": f"{perfil1.nombre} {perfil1.apellido}" if perfil1 else f"Usuario {pareja.jugador1_id}",
            "jugador2_nombre": f"{perfil2.nombre} {perfil2.apellido}" if perfil2 else f"Usuario {pareja.jugador2_id}",
            "pago_monto": float(pareja.pago_monto) if pareja.pago_monto else None,
            "pago_comprobante_url": pareja.pago_comprobante_url,
            "created_at": pareja.created_at.isoformat() if pareja.created_at else None
        })
    
    return {
        "total": len(resultado),
        "parejas": resultado
    }


# ============================================
# ENDPOINTS DE CAMBIO DE COMPAÑERO
# ============================================

@router.patch("/{torneo_id}/parejas/{pareja_id}/cambiar-companero")
async def cambiar_companero(
    torneo_id: int,
    pareja_id: int,
    data: CambiarCompaneroRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cambia el compañero de una pareja (después de rechazo)
    Solo accesible por el jugador1 (quien creó la inscripción)
    """
    pareja = db.query(TorneoPareja).filter(
        TorneoPareja.id == pareja_id,
        TorneoPareja.torneo_id == torneo_id
    ).first()
    
    if not pareja:
        raise HTTPException(status_code=404, detail="Pareja no encontrada")
    
    # Verificar que sea el jugador1
    if pareja.jugador1_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Solo el jugador que creó la inscripción puede cambiar de compañero")
    
    # Verificar que el jugador2 haya rechazado o la pareja esté pendiente
    if pareja.estado not in ['pendiente', 'rechazada']:
        raise HTTPException(status_code=400, detail="Solo se puede cambiar de compañero si la invitación fue rechazada o está pendiente")
    
    # Verificar que el nuevo jugador2 no sea el mismo que el jugador1
    if data.nuevo_jugador2_id == pareja.jugador1_id:
        raise HTTPException(status_code=400, detail="No puedes inscribirte contigo mismo")
    
    # Verificar que el nuevo jugador2 exista
    nuevo_jugador2 = db.query(Usuario).filter(Usuario.id_usuario == data.nuevo_jugador2_id).first()
    if not nuevo_jugador2:
        raise HTTPException(status_code=404, detail="El nuevo compañero no existe")
    
    # Guardar jugador2 anterior
    pareja.jugador2_anterior_id = pareja.jugador2_id
    pareja.fecha_cambio_jugador2 = datetime.now()
    pareja.motivo_cambio = data.motivo
    
    # Actualizar jugador2
    pareja.jugador2_id = data.nuevo_jugador2_id
    pareja.confirmado_jugador2 = False
    pareja.estado = 'pendiente'
    
    # Generar nuevo código de confirmación
    import string
    import random
    codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    pareja.codigo_confirmacion = codigo
    
    # Resetear pago si existía
    pareja.pago_estado = 'pendiente'
    pareja.pago_comprobante_url = None
    pareja.motivo_rechazo_pago = None
    
    db.commit()
    db.refresh(pareja)
    
    return {
        "mensaje": "Compañero cambiado exitosamente. Se ha enviado una nueva invitación.",
        "nuevo_jugador2_id": pareja.jugador2_id,
        "codigo_confirmacion": codigo
    }


@router.delete("/{torneo_id}/parejas/{pareja_id}/cancelar")
async def cancelar_inscripcion(
    torneo_id: int,
    pareja_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cancela la inscripción de una pareja
    Solo accesible por el jugador1 o un organizador
    """
    pareja = db.query(TorneoPareja).filter(
        TorneoPareja.id == pareja_id,
        TorneoPareja.torneo_id == torneo_id
    ).first()
    
    if not pareja:
        raise HTTPException(status_code=404, detail="Pareja no encontrada")
    
    # Verificar permisos
    es_organizador = TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario)
    es_jugador1 = pareja.jugador1_id == current_user.id_usuario
    
    if not (es_organizador or es_jugador1):
        raise HTTPException(status_code=403, detail="No tienes permisos para cancelar esta inscripción")
    
    # Si hay pago verificado, registrar para reembolso
    if pareja.pago_estado == 'verificado':
        historial = TorneoPagoHistorial(
            pareja_id=pareja.id,
            estado_anterior='verificado',
            estado_nuevo='reembolsado',
            monto=pareja.pago_monto,
            observaciones="Inscripción cancelada - Pendiente de reembolso",
            modificado_por=current_user.id_usuario
        )
        db.add(historial)
    
    # Marcar como baja en lugar de eliminar (para mantener historial)
    pareja.estado = 'baja'
    pareja.observaciones = f"{pareja.observaciones or ''}\nCancelada el {datetime.now().isoformat()}"
    
    db.commit()
    
    mensaje = "Inscripción cancelada exitosamente."
    if pareja.pago_estado == 'verificado':
        mensaje += " Por favor, comunícate con el organizador del torneo para coordinar la devolución del dinero."
    
    return {"mensaje": mensaje}


# ============================================
# ENDPOINTS DE DISPONIBILIDAD HORARIA
# ============================================

@router.patch("/{torneo_id}/parejas/{pareja_id}/disponibilidad")
async def actualizar_disponibilidad(
    torneo_id: int,
    pareja_id: int,
    data: ActualizarDisponibilidadRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza la disponibilidad horaria de una pareja
    Accesible por ambos jugadores de la pareja
    """
    pareja = db.query(TorneoPareja).filter(
        TorneoPareja.id == pareja_id,
        TorneoPareja.torneo_id == torneo_id
    ).first()
    
    if not pareja:
        raise HTTPException(status_code=404, detail="Pareja no encontrada")
    
    # Verificar que sea uno de los jugadores
    if pareja.jugador1_id != current_user.id_usuario and pareja.jugador2_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Solo los jugadores de la pareja pueden actualizar la disponibilidad")
    
    # Actualizar disponibilidad
    pareja.disponibilidad_horaria = data.disponibilidad_horaria.model_dump()
    
    db.commit()
    db.refresh(pareja)
    
    return {
        "mensaje": "Disponibilidad horaria actualizada exitosamente",
        "disponibilidad_horaria": pareja.disponibilidad_horaria
    }


@router.get("/{torneo_id}/disponibilidad-parejas")
async def obtener_disponibilidad_parejas(
    torneo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la disponibilidad horaria de todas las parejas del torneo
    Solo accesible por organizadores (para programación de partidos)
    """
    if not TorneoZonaService._es_organizador(db, torneo_id, current_user.id_usuario):
        raise HTTPException(status_code=403, detail="Solo los organizadores pueden ver la disponibilidad de las parejas")
    
    parejas = db.query(TorneoPareja).filter(
        TorneoPareja.torneo_id == torneo_id,
        TorneoPareja.estado.in_(['confirmada', 'inscripta'])
    ).all()
    
    resultado = []
    for pareja in parejas:
        resultado.append({
            "pareja_id": pareja.id,
            "jugador1_id": pareja.jugador1_id,
            "jugador2_id": pareja.jugador2_id,
            "disponibilidad_horaria": pareja.disponibilidad_horaria or {}
        })
    
    return {
        "total": len(resultado),
        "parejas": resultado
    }
