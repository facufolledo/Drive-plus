"""
Servicio para gestión básica de torneos
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime

from ..models.torneo_models import (
    Torneo, TorneoOrganizador, OrganizadorAutorizado,
    EstadoTorneo, RolOrganizador, TorneoCancha
)
from ..schemas.torneo_schemas import TorneoCreate, TorneoUpdate


class TorneoService:
    """Servicio para operaciones CRUD de torneos"""
    
    @staticmethod
    def es_organizador_autorizado(db: Session, user_id: int) -> bool:
        """Verifica si un usuario está autorizado para crear torneos"""
        from ..models.driveplus_models import Usuario
        usuario = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        return usuario and getattr(usuario, 'puede_crear_torneos', False)
    
    @staticmethod
    def es_organizador_torneo(db: Session, torneo_id: int, user_id: int) -> bool:
        """Verifica si un usuario es organizador de un torneo específico"""
        # Primero verificar si es el creador del torneo
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        if torneo and torneo.creado_por == user_id:
            return True
        
        # Luego verificar en la tabla de organizadores (si existe)
        try:
            org = db.query(TorneoOrganizador).filter(
                TorneoOrganizador.torneo_id == torneo_id,
                TorneoOrganizador.user_id == user_id
            ).first()
            return org is not None
        except Exception:
            # Si la tabla no existe o hay error, solo verificar creador
            return False
    
    @staticmethod
    def es_owner_torneo(db: Session, torneo_id: int, user_id: int) -> bool:
        """Verifica si un usuario es el owner de un torneo"""
        org = db.query(TorneoOrganizador).filter(
            TorneoOrganizador.torneo_id == torneo_id,
            TorneoOrganizador.user_id == user_id,
            TorneoOrganizador.rol == RolOrganizador.OWNER
        ).first()
        return org is not None
    
    @staticmethod
    def crear_torneo(db: Session, torneo_data: TorneoCreate, user_id: int) -> Torneo:
        """
        Crea un nuevo torneo
        
        Args:
            db: Sesión de base de datos
            torneo_data: Datos del torneo
            user_id: ID del usuario creador
            
        Returns:
            Torneo creado
            
        Raises:
            ValueError: Si el usuario no está autorizado
        """
        # Verificar que el usuario esté autorizado
        if not TorneoService.es_organizador_autorizado(db, user_id):
            raise ValueError("Usuario no autorizado para crear torneos")
        
        # Validar fechas
        if torneo_data.fecha_fin < torneo_data.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        
        # Validar género
        genero = torneo_data.genero if torneo_data.genero in ['masculino', 'femenino', 'mixto'] else 'masculino'
        
        # Procesar horarios disponibles
        # El frontend puede enviar {semana: [], finDeSemana: []} o un array directo
        horarios_procesados = []
        horarios_raw = getattr(torneo_data, 'horarios_disponibles', [])
        
        if isinstance(horarios_raw, dict):
            # Formato del frontend: {semana: [{desde, hasta}], finDeSemana: [{desde, hasta}]}
            if 'semana' in horarios_raw:
                for h in horarios_raw['semana']:
                    horarios_procesados.append({
                        'dias': ['lunes', 'martes', 'miercoles', 'jueves'],
                        'horaInicio': h.get('desde', '09:00'),
                        'horaFin': h.get('hasta', '23:00')
                    })
            if 'finDeSemana' in horarios_raw:
                for h in horarios_raw['finDeSemana']:
                    horarios_procesados.append({
                        'dias': ['viernes', 'sabado', 'domingo'],
                        'horaInicio': h.get('desde', '09:00'),
                        'horaFin': h.get('hasta', '23:00')
                    })
        elif isinstance(horarios_raw, list):
            # Ya viene en formato correcto
            horarios_procesados = horarios_raw
        
        # Crear torneo
        torneo = Torneo(
            nombre=torneo_data.nombre,
            descripcion=torneo_data.descripcion,
            categoria=torneo_data.categoria,
            genero=genero,
            fecha_inicio=torneo_data.fecha_inicio,
            fecha_fin=torneo_data.fecha_fin,
            lugar=torneo_data.lugar,
            reglas_json=torneo_data.reglas_json,
            creado_por=user_id,
            estado=EstadoTorneo.INSCRIPCION,
            # Campos de pago (con valores por defecto si no vienen)
            requiere_pago=getattr(torneo_data, 'requiere_pago', False),
            monto_inscripcion=getattr(torneo_data, 'monto_inscripcion', 0),
            alias_cbu_cvu=getattr(torneo_data, 'alias_cbu_cvu', None),
            titular_cuenta=getattr(torneo_data, 'titular_cuenta', None),
            banco=getattr(torneo_data, 'banco', None),
            telefono_contacto=getattr(torneo_data, 'telefono_contacto', None),
            # Horarios disponibles procesados
            horarios_disponibles=horarios_procesados
        )
        
        db.add(torneo)
        db.flush()  # Para obtener el ID
        
        # Agregar al creador como owner
        organizador = TorneoOrganizador(
            torneo_id=torneo.id,
            user_id=user_id,
            rol=RolOrganizador.OWNER
        )
        db.add(organizador)
        
        # Crear canchas automáticamente si se especificaron en reglas_json
        if torneo_data.reglas_json and 'canchas_disponibles' in torneo_data.reglas_json:
            num_canchas = torneo_data.reglas_json['canchas_disponibles']
            for i in range(1, num_canchas + 1):
                cancha = TorneoCancha(
                    torneo_id=torneo.id,
                    nombre=f"Cancha {i}",
                    activa=True
                )
                db.add(cancha)
        
        db.commit()
        db.refresh(torneo)
        
        return torneo
    
    @staticmethod
    def obtener_torneo(db: Session, torneo_id: int) -> Optional[Torneo]:
        """Obtiene un torneo por ID"""
        return db.query(Torneo).filter(Torneo.id == torneo_id).first()
    
    @staticmethod
    def listar_torneos(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[str] = None,
        categoria: Optional[str] = None
    ) -> List[Torneo]:
        """
        Lista torneos con filtros opcionales
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            estado: Filtrar por estado
            categoria: Filtrar por categoría
            
        Returns:
            Lista de torneos
        """
        query = db.query(Torneo)
        
        if estado:
            query = query.filter(Torneo.estado == estado)
        
        if categoria:
            query = query.filter(Torneo.categoria == categoria)
        
        return query.order_by(Torneo.fecha_inicio.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def actualizar_torneo(
        db: Session,
        torneo_id: int,
        torneo_data: TorneoUpdate,
        user_id: int
    ) -> Torneo:
        """
        Actualiza un torneo
        
        Args:
            db: Sesión de base de datos
            torneo_id: ID del torneo
            torneo_data: Datos a actualizar
            user_id: ID del usuario que actualiza
            
        Returns:
            Torneo actualizado
            
        Raises:
            ValueError: Si el usuario no tiene permisos o el torneo no existe
        """
        # Verificar permisos
        if not TorneoService.es_organizador_torneo(db, torneo_id, user_id):
            raise ValueError("No tienes permisos para editar este torneo")
        
        # Obtener torneo
        torneo = TorneoService.obtener_torneo(db, torneo_id)
        if not torneo:
            raise ValueError("Torneo no encontrado")
        
        # Actualizar campos
        if torneo_data.nombre is not None:
            torneo.nombre = torneo_data.nombre
        
        if torneo_data.descripcion is not None:
            torneo.descripcion = torneo_data.descripcion
        
        if torneo_data.categoria is not None:
            torneo.categoria = torneo_data.categoria
        
        if torneo_data.fecha_inicio is not None:
            torneo.fecha_inicio = torneo_data.fecha_inicio
        
        if torneo_data.fecha_fin is not None:
            torneo.fecha_fin = torneo_data.fecha_fin
        
        if torneo_data.lugar is not None:
            torneo.lugar = torneo_data.lugar
        
        if torneo_data.reglas_json is not None:
            torneo.reglas_json = torneo_data.reglas_json
        
        if torneo_data.estado is not None:
            torneo.estado = torneo_data.estado
        
        # Validar fechas
        if torneo.fecha_fin < torneo.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        
        db.commit()
        db.refresh(torneo)
        
        return torneo
    
    @staticmethod
    def eliminar_torneo(db: Session, torneo_id: int, user_id: int) -> bool:
        """
        Elimina un torneo (solo el owner puede hacerlo)
        
        Args:
            db: Sesión de base de datos
            torneo_id: ID del torneo
            user_id: ID del usuario
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            ValueError: Si no tiene permisos o el torneo no existe
        """
        # Verificar que sea el owner
        if not TorneoService.es_owner_torneo(db, torneo_id, user_id):
            raise ValueError("Solo el owner puede eliminar el torneo")
        
        # Obtener torneo
        torneo = TorneoService.obtener_torneo(db, torneo_id)
        if not torneo:
            raise ValueError("Torneo no encontrado")
        
        # No permitir eliminar si ya tiene partidos jugados
        if torneo.estado not in [EstadoTorneo.INSCRIPCION, EstadoTorneo.ARMANDO_ZONAS]:
            raise ValueError("No se puede eliminar un torneo que ya comenzó")
        
        db.delete(torneo)
        db.commit()
        
        return True
    
    @staticmethod
    def agregar_organizador(
        db: Session,
        torneo_id: int,
        nuevo_organizador_id: int,
        user_id: int,
        rol: str = "colaborador"
    ) -> TorneoOrganizador:
        """
        Agrega un organizador al torneo
        
        Args:
            db: Sesión de base de datos
            torneo_id: ID del torneo
            nuevo_organizador_id: ID del usuario a agregar
            user_id: ID del usuario que agrega (debe ser owner)
            rol: Rol del nuevo organizador
            
        Returns:
            TorneoOrganizador creado
            
        Raises:
            ValueError: Si no tiene permisos o ya existe
        """
        # Verificar que sea el owner
        if not TorneoService.es_owner_torneo(db, torneo_id, user_id):
            raise ValueError("Solo el owner puede agregar organizadores")
        
        # Verificar que no exista ya
        existe = db.query(TorneoOrganizador).filter(
            TorneoOrganizador.torneo_id == torneo_id,
            TorneoOrganizador.user_id == nuevo_organizador_id
        ).first()
        
        if existe:
            raise ValueError("El usuario ya es organizador de este torneo")
        
        # Crear organizador
        organizador = TorneoOrganizador(
            torneo_id=torneo_id,
            user_id=nuevo_organizador_id,
            rol=RolOrganizador.COLABORADOR if rol == "colaborador" else RolOrganizador.OWNER
        )
        
        db.add(organizador)
        db.commit()
        db.refresh(organizador)
        
        return organizador
    
    @staticmethod
    def remover_organizador(
        db: Session,
        torneo_id: int,
        organizador_id: int,
        user_id: int
    ) -> bool:
        """
        Remueve un organizador del torneo
        
        Args:
            db: Sesión de base de datos
            torneo_id: ID del torneo
            organizador_id: ID del organizador a remover
            user_id: ID del usuario que remueve (debe ser owner)
            
        Returns:
            True si se removió correctamente
            
        Raises:
            ValueError: Si no tiene permisos o no existe
        """
        # Verificar que sea el owner
        if not TorneoService.es_owner_torneo(db, torneo_id, user_id):
            raise ValueError("Solo el owner puede remover organizadores")
        
        # No permitir remover al owner
        organizador = db.query(TorneoOrganizador).filter(
            TorneoOrganizador.torneo_id == torneo_id,
            TorneoOrganizador.user_id == organizador_id
        ).first()
        
        if not organizador:
            raise ValueError("Organizador no encontrado")
        
        if organizador.rol == RolOrganizador.OWNER:
            raise ValueError("No se puede remover al owner del torneo")
        
        db.delete(organizador)
        db.commit()
        
        return True
    
    @staticmethod
    def listar_organizadores(db: Session, torneo_id: int) -> List[TorneoOrganizador]:
        """Lista todos los organizadores de un torneo"""
        return db.query(TorneoOrganizador).filter(
            TorneoOrganizador.torneo_id == torneo_id
        ).all()
    
    @staticmethod
    def cambiar_estado(
        db: Session,
        torneo_id: int,
        nuevo_estado: str,
        user_id: int
    ) -> Torneo:
        """
        Cambia el estado de un torneo
        
        Args:
            db: Sesión de base de datos
            torneo_id: ID del torneo
            nuevo_estado: Nuevo estado
            user_id: ID del usuario
            
        Returns:
            Torneo actualizado
            
        Raises:
            ValueError: Si no tiene permisos o transición inválida
        """
        # Verificar permisos
        if not TorneoService.es_organizador_torneo(db, torneo_id, user_id):
            raise ValueError("No tienes permisos para cambiar el estado")
        
        # Obtener torneo
        torneo = TorneoService.obtener_torneo(db, torneo_id)
        if not torneo:
            raise ValueError("Torneo no encontrado")
        
        # Validar transiciones de estado
        transiciones_validas = {
            EstadoTorneo.INSCRIPCION: [EstadoTorneo.ARMANDO_ZONAS],
            EstadoTorneo.ARMANDO_ZONAS: [EstadoTorneo.FASE_GRUPOS, EstadoTorneo.INSCRIPCION],
            EstadoTorneo.FASE_GRUPOS: [EstadoTorneo.FASE_ELIMINACION],
            EstadoTorneo.FASE_ELIMINACION: [EstadoTorneo.FINALIZADO],
        }
        
        if nuevo_estado not in [e.value for e in transiciones_validas.get(torneo.estado, [])]:
            raise ValueError(f"Transición de estado inválida: {torneo.estado} -> {nuevo_estado}")
        
        torneo.estado = nuevo_estado
        db.commit()
        db.refresh(torneo)
        
        return torneo
