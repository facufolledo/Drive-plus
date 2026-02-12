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
    nombre: str = Field(..., min_length=1, max_length=50)  # "8va", "6ta", "4ta", "Libre"
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
    telefono_contacto: Optional[str] = Field(None, description="Telefono para enviar comprobante de pago")

    # Horarios disponibles del torneo
    horarios_disponibles: Optional[Any] = Field(default_factory=list, description="Horarios disponibles")

    # Codigo de circuito
    codigo: Optional[str] = Field(None, max_length=20, description="Codigo de circuito")

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

    # Codigo de circuito
    codigo: Optional[str] = None

    class Config:
        from_attributes = True


# Schemas para Pareja
class ParejaInscripcion(BaseModel):
    jugador1_id: int
    jugador2_id: int
    categoria_id: Optional[int] = None  # ID de la categoría del torneo
    nombre_pareja: Optional[str] = None
    observaciones: Optional[str] = None
    
    @validator('jugador2_id')
    def validar_jugadores_diferentes(cls, v, values):
        if 'jugador1_id' in values and v == values['jugador1_id']:
            raise ValueError('Los jugadores deben ser diferentes')
        return v


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
