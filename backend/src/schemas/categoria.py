from pydantic import BaseModel
from typing import Optional

class CategoriaBase(BaseModel):
    """Esquema base para categorías"""
    nombre: str
    descripcion: Optional[str] = None
    rating_min: Optional[int] = None
    rating_max: Optional[int] = None
    sexo: Optional[str] = "masculino"

class CategoriaCreate(CategoriaBase):
    """Esquema para crear una categoría"""
    pass

class CategoriaUpdate(CategoriaBase):
    """Esquema para actualizar una categoría"""
    nombre: Optional[str] = None

class CategoriaResponse(CategoriaBase):
    """Esquema para respuesta de categoría"""
    id_categoria: int
    
    class Config:
        from_attributes = True

class CategoriaList(BaseModel):
    """Esquema para lista de categorías"""
    categorias: list[CategoriaResponse]
    total: int

class JugadorCategoriaResponse(BaseModel):
    """Esquema para respuesta de jugador en categoría"""
    id_usuario: int
    nombre_usuario: str
    nombre: Optional[str] = ""
    apellido: Optional[str] = ""
    rating: int
    partidos_jugados: int
    partidos_ganados: Optional[int] = 0
    sexo: str
    imagen_url: Optional[str] = None
    tendencia: Optional[str] = "neutral"
    
    class Config:
        from_attributes = True

class JugadoresPorCategoriaResponse(BaseModel):
    """Esquema para respuesta de jugadores por categoría"""
    categoria: CategoriaResponse
    jugadores: list[JugadorCategoriaResponse]
    total_jugadores: int

