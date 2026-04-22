"""
Schemas Pydantic para el sistema de torneos
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import date, datetime, time
from enum import Enum


# Enums
class EstadoTorneoEnum(str, Enum):
    INSCRIPCION = "inscripcion"
    ARMANDO_ZONAS = "armando_zonas"
    FASE_GRUPOS = "fase_grupos"
    FASE_ELIMINACION = "fase_eliminacion"
    FINALIZADO = "finalizado"


class EstadoParejaEnum(str, Enum):
    INSCRIPTA = "inscripta"
    CONFIRMADA = "confirmada"
    BAJA = "baja"


class FasePartidoEnum(str, Enum):
    ZONA = "zona"
    DIECISEISAVOS = "16avos"
    OCTAVOS = "8vos"
    CUARTOS = "4tos"
    SEMIS = "semis"
    FINAL = "final"


class EstadoPartidoEnum(str, Enum):
    PENDIENTE = "pendiente"
    EN_JUEGO = "en_juego"
    FINALIZADO = "finalizado"
    WO = "w_o"
    CANCELADO = "cancelado"


# Schemas para Categoría de Torneo
class CategoriaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50)  # "8va", "6ta", "4ta", "3ra"
    genero: str = Field(default="masculino")  # masculino, femenino, mixto
    max_parejas: int = Field(default=16, ge=2, le=64)
    orden: int = Field(default=0)


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)
    genero: Optional[str] = None
    max_parejas: Optional[int] = Field(None, ge=2, le=64)
    estado: Optional[str] = None
    orden: Optional[int] = None


class CategoriaResponse(BaseModel):
    id: int
    torneo_id: int
    nombre: str
    genero: str
    max_parejas: int
    estado: str
    orden: int
    parejas_inscritas: Optional[int] = 0
    
    class Config:
        from_attributes = True


# Schemas para Torneo
class TorneoCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=255)
    descripcion: Optional[str] = None
    categoria: str = Field(..., min_length=2, max_length=50)
    genero: Optional[str] = Field(default="masculino")  # masculino, femenino, mixto
    fecha_inicio: date
    fecha_fin: date
    lugar: Optional[str] = None
    reglas_json: Optional[dict] = Field(default_factory=lambda: {
        "puntos_victoria": 3,
        "puntos_derrota": 0,
        "sets_para_ganar": 2
    })
    
    # Campos de pago
    requiere_pago: Optional[bool] = Field(default=False)
    monto_inscripcion: Optional[float] = Field(default=0)
    alias_cbu_cvu: Optional[str] = None
    titular_cuenta: Optional[str] = None
    banco: Optional[str] = None
    telefono_contacto: Optional[str] = Field(None, description="Teléfono para enviar comprobante de pago (ej: +54 9 11 1234-5678)")
    
    # Horarios disponibles del torneo (puede ser lista o dict {semana: [], finDeSemana: []})
    horarios_disponibles: Optional[Any] = Field(default_factory=list, description="Horarios disponibles: lista o dict {semana: [], finDeSemana: []}")
    
    # Código de circuito
    codigo: Optional[str] = Field(None, max_length=20, description="Código de circuito (ej: 'zf' para Zona Fitness)")
    
    @validator('fecha_fin')
    def validar_fechas(cls, v, values):
        if 'fecha_inicio' in values and v < values['fecha_inicio']:
            raise ValueError('fecha_fin debe ser posterior a fecha_inicio')
        return v


class TorneoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=255)
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    lugar: Optional[str] = None
    reglas_json: Optional[dict] = None
    estado: Optional[EstadoTorneoEnum] = None


class TorneoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    tipo: str
    categoria: str
    estado: EstadoTorneoEnum
    fecha_inicio: date
    fecha_fin: date
    lugar: Optional[str]
    reglas_json: Optional[dict]
    creado_por: int
    created_at: datetime
    updated_at: datetime
    parejas_inscritas: Optional[int] = 0
    
    # Campos de pago
    requiere_pago: Optional[bool] = False
    monto_inscripcion: Optional[float] = 0
    alias_cbu_cvu: Optional[str] = None
    titular_cuenta: Optional[str] = None
    banco: Optional[str] = None
    telefono_contacto: Optional[str] = None
    
    # Horarios
    horarios_disponibles: Optional[Any] = None
    total_partidos: Optional[int] = 0
    
    # Código de circuito
    codigo: Optional[str] = None
    
    class Config:
        from_attributes = True


# Schemas para Pareja
class ParejaInscripcion(BaseModel):
    jugador1_id: int
    jugador2_id: int
    categoria_id: Optional[int] = Field(default=None)  # ID de la categoría del torneo
    nombre_pareja: Optional[str] = Field(default=None)
    observaciones: Optional[str] = Field(default=None)
    disponibilidad_horaria: Optional[List[dict]] = Field(default=None, description="Array de restricciones: [{dias: [], horaInicio: '', horaFin: ''}]")
    
    @validator('jugador2_id')
    def validar_jugadores_diferentes(cls, v, values):
        if 'jugador1_id' in values and v == values['jugador1_id']:
            raise ValueError('Los jugadores deben ser diferentes')
        return v
    
    class Config:
        # Permitir campos extra y no excluir None
        extra = 'allow'


class ParejaUpdate(BaseModel):
    jugador1_id: Optional[int] = None
    jugador2_id: Optional[int] = None
    estado: Optional[EstadoParejaEnum] = None
    categoria_id: Optional[int] = None  # Para cambiar de categoría
    categoria_asignada: Optional[str] = None
    observaciones: Optional[str] = None


class JugadorBasico(BaseModel):
    id: int
    nombre: str
    apellido: str
    foto_perfil: Optional[str]
    rating: Optional[float]
    categoria: Optional[str]
    
    class Config:
        from_attributes = True


class ParejaResponse(BaseModel):
    id: int
    torneo_id: int
    jugador1: JugadorBasico
    jugador2: JugadorBasico
    estado: EstadoParejaEnum
    categoria_asignada: Optional[str]
    observaciones: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Schemas para Zona
class ZonaResponse(BaseModel):
    id: int
    torneo_id: int
    nombre: str
    numero_orden: int
    parejas: List[ParejaResponse]
    
    class Config:
        from_attributes = True


# Schemas para Cancha
class CanchaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)


class CanchaResponse(BaseModel):
    id: int
    torneo_id: int
    nombre: str
    activa: bool
    
    class Config:
        from_attributes = True


# Schemas para Slot
class SlotCreate(BaseModel):
    cancha_id: int
    fecha_hora_inicio: datetime
    fecha_hora_fin: datetime
    
    @validator('fecha_hora_fin')
    def validar_horarios(cls, v, values):
        if 'fecha_hora_inicio' in values and v <= values['fecha_hora_inicio']:
            raise ValueError('fecha_hora_fin debe ser posterior a fecha_hora_inicio')
        return v


class SlotResponse(BaseModel):
    id: int
    torneo_id: int
    cancha_id: int
    fecha_hora_inicio: datetime
    fecha_hora_fin: datetime
    ocupado: bool
    partido_id: Optional[int]
    
    class Config:
        from_attributes = True


# Schemas para Bloqueo de Jugador
class BloqueoJugadorCreate(BaseModel):
    fecha: date
    hora_desde: str = Field(..., pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    hora_hasta: str = Field(..., pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    motivo: Optional[str] = None
    
    @validator('hora_hasta')
    def validar_horarios(cls, v, values):
        if 'hora_desde' in values and v <= values['hora_desde']:
            raise ValueError('hora_hasta debe ser posterior a hora_desde')
        return v


class BloqueoJugadorResponse(BaseModel):
    id: int
    torneo_id: int
    jugador_id: int
    fecha: date
    hora_desde: str
    hora_hasta: str
    motivo: Optional[str]
    
    class Config:
        from_attributes = True


# Schemas para Partido
class SetCreate(BaseModel):
    numero_set: int = Field(..., ge=1, le=3)
    games_pareja1: int = Field(..., ge=0, le=7)
    games_pareja2: int = Field(..., ge=0, le=7)
    es_tiebreak: bool = False


class SetResponse(BaseModel):
    id: int
    numero_set: int
    games_pareja1: int
    games_pareja2: int
    es_tiebreak: bool
    
    class Config:
        from_attributes = True


class ResultadoPartidoCreate(BaseModel):
    sets: List[SetCreate] = Field(..., min_items=2, max_items=3)
    
    @validator('sets')
    def validar_sets(cls, v):
        # Validar que haya un ganador claro
        sets_p1 = sum(1 for s in v if s.games_pareja1 > s.games_pareja2)
        sets_p2 = sum(1 for s in v if s.games_pareja2 > s.games_pareja1)
        
        if sets_p1 == sets_p2:
            raise ValueError('Debe haber un ganador claro')
        
        if max(sets_p1, sets_p2) < 2:
            raise ValueError('El ganador debe ganar al menos 2 sets')
        
        return v


class PartidoResponse(BaseModel):
    id: int
    torneo_id: int
    zona_id: Optional[int]
    fase: FasePartidoEnum
    numero_partido: Optional[int]
    pareja1: ParejaResponse
    pareja2: ParejaResponse
    cancha_id: Optional[int]
    cancha_nombre: Optional[str]
    fecha_hora: Optional[datetime]
    estado: EstadoPartidoEnum
    ganador_pareja_id: Optional[int]
    sets: List[SetResponse]
    requiere_reprogramacion: bool
    observaciones: Optional[str]
    
    class Config:
        from_attributes = True


# Schemas para Tabla de Posiciones
class TablaPosicionesResponse(BaseModel):
    posicion: int
    pareja: ParejaResponse
    puntos: int
    partidos_jugados: int
    partidos_ganados: int
    partidos_perdidos: int
    sets_favor: int
    sets_contra: int
    diferencia_sets: int
    games_favor: int
    games_contra: int
    diferencia_games: int
    
    class Config:
        from_attributes = True


# Schemas para operaciones especiales
class GenerarZonasRequest(BaseModel):
    mezclar_aleatoriamente: bool = True


class GenerarZonasResponse(BaseModel):
    zonas_creadas: int
    parejas_por_zona: List[int]
    mensaje: str


class GenerarCuadroEliminacionResponse(BaseModel):
    fase_inicial: FasePartidoEnum
    clasificados: int
    byes: int
    partidos_generados: int
    mensaje: str


class ReemplazarJugadorRequest(BaseModel):
    pareja_id: int
    jugador_saliente_id: int
    jugador_entrante_id: int


class MoverParejaZonaRequest(BaseModel):
    pareja_id: int
    zona_destino_id: int


class ReprogramarPartidoRequest(BaseModel):
    partido_id: int
    cancha_id: int
    fecha_hora: datetime


# Schemas para estadísticas
class EstadisticasTorneoResponse(BaseModel):
    torneo_id: int
    total_parejas: int
    total_partidos: int
    partidos_jugados: int
    partidos_pendientes: int
    zonas: int
    fase_actual: EstadoTorneoEnum
    
    class Config:
        from_attributes = True


# ============================================
# SCHEMAS PARA PAGOS
# ============================================

class DisponibilidadHoraria(BaseModel):
    """Disponibilidad horaria por día de la semana"""
    lunes: Optional[List[str]] = []
    martes: Optional[List[str]] = []
    miercoles: Optional[List[str]] = []
    jueves: Optional[List[str]] = []
    viernes: Optional[List[str]] = []
    sabado: Optional[List[str]] = ['todo_el_dia']
    domingo: Optional[List[str]] = ['todo_el_dia']
    
    class Config:
        json_schema_extra = {
            "example": {
                "lunes": ["08:00-10:00", "17:00-19:00"],
                "martes": ["17:00-21:00"],
                "jueves": ["17:00-21:00"],
                "viernes": ["17:00-21:00"],
                "sabado": ["todo_el_dia"],
                "domingo": ["todo_el_dia"]
            }
        }


class SubirComprobanteRequest(BaseModel):
    """Request para subir comprobante de pago"""
    comprobante_url: str


class VerificarPagoRequest(BaseModel):
    """Request para verificar pago (organizador)"""
    aprobado: bool
    motivo_rechazo: Optional[str] = None


class CambiarCompaneroRequest(BaseModel):
    """Request para cambiar de compañero"""
    nuevo_jugador2_id: int
    motivo: Optional[str] = "Compañero anterior rechazó la invitación"


class ActualizarDisponibilidadRequest(BaseModel):
    """Request para actualizar disponibilidad horaria"""
    disponibilidad_horaria: DisponibilidadHoraria


class DatosPagoResponse(BaseModel):
    """Response con datos de pago del torneo"""
    requiere_pago: bool
    monto_inscripcion: Optional[float] = None
    alias_cbu_cvu: Optional[str] = None
    titular_cuenta: Optional[str] = None
    banco: Optional[str] = None
    telefono_contacto: Optional[str] = None
    
    class Config:
        from_attributes = True


class EstadoPagoResponse(BaseModel):
    """Response con estado de pago de una pareja"""
    pareja_id: int
    pago_estado: str
    pago_monto: Optional[float] = None
    pago_comprobante_url: Optional[str] = None
    pago_fecha_acreditacion: Optional[str] = None
    motivo_rechazo_pago: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# Schemas para Sistema de Pagos
# ============================================

class SubirComprobanteRequest(BaseModel):
    """Request para subir comprobante de pago"""
    comprobante_url: str
    
class VerificarPagoRequest(BaseModel):
    """Request para verificar/rechazar pago"""
    aprobado: bool
    motivo_rechazo: Optional[str] = None

class CambiarCompaneroRequest(BaseModel):
    """Request para cambiar de compañero"""
    nuevo_jugador2_id: int
    motivo: Optional[str] = None

class ActualizarDisponibilidadRequest(BaseModel):
    """Request para actualizar disponibilidad horaria"""
    disponibilidad_horaria: dict  # JSON con formato: {"lunes": ["08:00-10:00"], ...}

class DatosPagoResponse(BaseModel):
    """Response con datos de pago del torneo"""
    requiere_pago: bool
    monto_inscripcion: Optional[float] = None
    alias_cbu_cvu: Optional[str] = None
    titular_cuenta: Optional[str] = None
    banco: Optional[str] = None

class EstadoPagoResponse(BaseModel):
    """Response con estado de pago de una pareja"""
    pareja_id: int
    pago_estado: str
    pago_monto: Optional[float] = None
    pago_comprobante_url: Optional[str] = None
    pago_fecha_acreditacion: Optional[str] = None
    motivo_rechazo_pago: Optional[str] = None


# ============================================
# Schemas para Carga Masiva de Resultados
# ============================================

class ResultadoSimplificado(BaseModel):
    """
    Resultado simplificado para carga rápida
    Formato: "6-4 6-3" o "6-4 4-6 7-5"
    """
    partido_id: int
    resultado_texto: str = Field(..., description="Formato: '6-4 6-3' o '6-4 4-6 7-5'")
    
    @validator('resultado_texto')
    def validar_formato(cls, v):
        """Valida que el formato sea correcto"""
        import re
        # Formato: "6-4 6-3" o "6-4 4-6 7-5" (2 o 3 sets)
        pattern = r'^(\d{1,2}-\d{1,2})(\s+\d{1,2}-\d{1,2}){1,2}$'
        if not re.match(pattern, v.strip()):
            raise ValueError('Formato inválido. Use: "6-4 6-3" o "6-4 4-6 7-5"')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "partido_id": 123,
                "resultado_texto": "6-4 6-3"
            }
        }


class ResultadoMasivoRequest(BaseModel):
    """Request para cargar múltiples resultados a la vez"""
    resultados: List[ResultadoSimplificado] = Field(..., min_items=1, max_items=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "resultados": [
                    {"partido_id": 123, "resultado_texto": "6-4 6-3"},
                    {"partido_id": 124, "resultado_texto": "6-4 4-6 7-5"},
                    {"partido_id": 125, "resultado_texto": "6-2 6-1"}
                ]
            }
        }


class ResultadoMasivoItem(BaseModel):
    """Item individual del resultado masivo"""
    partido_id: int
    exito: bool
    mensaje: str
    ganador_pareja_id: Optional[int] = None
    error: Optional[str] = None


class ResultadoMasivoResponse(BaseModel):
    """Response de carga masiva de resultados"""
    total: int
    exitosos: int
    fallidos: int
    resultados: List[ResultadoMasivoItem]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 3,
                "exitosos": 2,
                "fallidos": 1,
                "resultados": [
                    {
                        "partido_id": 123,
                        "exito": True,
                        "mensaje": "Resultado cargado correctamente",
                        "ganador_pareja_id": 45
                    },
                    {
                        "partido_id": 124,
                        "exito": True,
                        "mensaje": "Resultado cargado correctamente",
                        "ganador_pareja_id": 47
                    },
                    {
                        "partido_id": 125,
                        "exito": False,
                        "mensaje": "Error al cargar resultado",
                        "error": "Partido ya tiene resultado"
                    }
                ]
            }
        }
