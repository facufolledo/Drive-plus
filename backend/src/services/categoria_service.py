"""
Servicio para gestión de categorías
"""
from sqlalchemy.orm import Session
from typing import Optional
from ..models.driveplus_models import Categoria, Usuario


def _normalizar_sexo(sexo: Optional[str]) -> str:
    """Normaliza sexo a 'masculino' o 'femenino' (Categoria usa estos valores)"""
    if not sexo:
        return "masculino"
    s = str(sexo).upper()
    if s in ("M", "MASCULINO", "MALE"):
        return "masculino"
    if s in ("F", "FEMENINO", "FEMALE"):
        return "femenino"
    return "masculino"


def actualizar_categoria_usuario(db: Session, usuario: Usuario) -> Optional[Categoria]:
    """
    Actualiza la categoría de un usuario según su rating actual.
    Cuando sube de rating (ej: 7ma 1199 → 1200), pasa a 6ta automáticamente.
    
    Args:
        db: Sesión de base de datos
        usuario: Usuario a actualizar
        
    Returns:
        La nueva categoría asignada o None si no se encontró
    """
    sexo_norm = _normalizar_sexo(usuario.sexo)
    # Buscar la categoría que corresponde al rating y sexo del usuario
    nueva_categoria = db.query(Categoria).filter(
        Categoria.sexo == sexo_norm,
        (Categoria.rating_min.is_(None) | (Categoria.rating_min <= usuario.rating)),
        (Categoria.rating_max.is_(None) | (Categoria.rating_max >= usuario.rating))
    ).order_by(Categoria.rating_min.desc()).first()
    
    if nueva_categoria:
        usuario.id_categoria = nueva_categoria.id_categoria
        return nueva_categoria
    
    return None


def obtener_categoria_por_rating(db: Session, rating: int, sexo: str) -> Optional[Categoria]:
    """
    Obtiene la categoría que corresponde a un rating y sexo específicos
    
    Args:
        db: Sesión de base de datos
        rating: Rating del jugador
        sexo: Sexo del jugador ('M' o 'F')
        
    Returns:
        La categoría correspondiente o None si no se encontró
    """
    categoria = db.query(Categoria).filter(
        Categoria.sexo == sexo,
        (Categoria.rating_min.is_(None) | (Categoria.rating_min <= rating)),
        (Categoria.rating_max.is_(None) | (Categoria.rating_max >= rating))
    ).order_by(Categoria.rating_min.desc()).first()
    
    return categoria
