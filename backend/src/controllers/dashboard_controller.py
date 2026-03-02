from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import Optional
from ..database import get_db
from ..models.usuario_models import Usuario
from ..models.partido_models import Partido, PartidoJugador, ResultadoPartido
from ..models.historial_rating_models import HistorialRating
from ..auth.jwt_handler import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/data")
async def get_dashboard_data(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint optimizado que trae todos los datos del dashboard en una sola llamada.
    Evita N+1 queries y reduce latencia.
    """
    try:
        # 1. Top 10 jugadores por sexo (una sola query con UNION)
        top_masculino = db.query(
            Usuario.id_usuario,
            Usuario.nombre,
            Usuario.apellido,
            Usuario.rating,
            Usuario.nombre_usuario,
            Usuario.sexo
        ).filter(
            Usuario.sexo.in_(['masculino', 'M']),
            Usuario.rating.isnot(None)
        ).order_by(desc(Usuario.rating)).limit(5).all()
        
        top_femenino = db.query(
            Usuario.id_usuario,
            Usuario.nombre,
            Usuario.apellido,
            Usuario.rating,
            Usuario.nombre_usuario,
            Usuario.sexo
        ).filter(
            Usuario.sexo.in_(['femenino', 'F']),
            Usuario.rating.isnot(None)
        ).order_by(desc(Usuario.rating)).limit(5).all()
        
        # 2. Últimos 3 partidos del usuario con resultado (una query optimizada)
        ultimos_partidos = db.query(
            Partido.id_partido,
            Partido.fecha,
            ResultadoPartido.sets_eq1,
            ResultadoPartido.sets_eq2,
            PartidoJugador.equipo,
            HistorialRating.delta
        ).join(
            PartidoJugador, Partido.id_partido == PartidoJugador.id_partido
        ).outerjoin(
            ResultadoPartido, Partido.id_partido == ResultadoPartido.id_partido
        ).outerjoin(
            HistorialRating, 
            (HistorialRating.id_partido == Partido.id_partido) & 
            (HistorialRating.id_usuario == current_user.id_usuario)
        ).filter(
            PartidoJugador.id_usuario == current_user.id_usuario,
            Partido.estado.in_(['finalizado', 'completado'])
        ).order_by(desc(Partido.fecha)).limit(3).all()
        
        # Procesar resultados de partidos
        partidos_data = []
        for p in ultimos_partidos:
            victoria = False
            if p.delta is not None:
                victoria = p.delta > 0
            elif p.sets_eq1 is not None and p.sets_eq2 is not None:
                if p.equipo == 1:
                    victoria = p.sets_eq1 > p.sets_eq2
                else:
                    victoria = p.sets_eq2 > p.sets_eq1
            
            partidos_data.append({
                "id_partido": p.id_partido,
                "fecha": p.fecha.isoformat() if p.fecha else None,
                "victoria": victoria
            })
        
        # 3. Calcular delta de la semana (una query)
        hace_7_dias = func.now() - func.cast('7 days', func.Interval)
        delta_semana = db.query(
            func.coalesce(func.sum(HistorialRating.delta), 0)
        ).filter(
            HistorialRating.id_usuario == current_user.id_usuario,
            HistorialRating.fecha >= hace_7_dias
        ).scalar()
        
        return {
            "top_jugadores": {
                "masculino": [
                    {
                        "id_usuario": j.id_usuario,
                        "nombre": j.nombre,
                        "apellido": j.apellido,
                        "rating": j.rating,
                        "nombre_usuario": j.nombre_usuario
                    } for j in top_masculino
                ],
                "femenino": [
                    {
                        "id_usuario": j.id_usuario,
                        "nombre": j.nombre,
                        "apellido": j.apellido,
                        "rating": j.rating,
                        "nombre_usuario": j.nombre_usuario
                    } for j in top_femenino
                ]
            },
            "ultimos_partidos": partidos_data,
            "delta_semana": int(delta_semana) if delta_semana else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar dashboard: {str(e)}")
