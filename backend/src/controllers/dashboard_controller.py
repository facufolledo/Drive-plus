"""
Controller optimizado para Dashboard - trae todos los datos en una sola query
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta

from ..database.config import get_db
from ..models.driveplus_models import Usuario, PerfilUsuario, Partido, PartidoJugador, ResultadoPartido, HistorialRating
from ..auth.auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/data")
async def obtener_datos_dashboard(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint optimizado que trae TODOS los datos del dashboard en una sola llamada:
    - Top 5 masculino
    - Top 5 femenino
    - Últimos 3 partidos del usuario
    - Delta de rating semanal
    """
    try:
        user_id = current_user.id_usuario
        
        # 1. Top 5 masculino (una sola query con join)
        top_masculino = db.query(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Usuario.rating,
            Usuario.sexo,
            PerfilUsuario.nombre,
            PerfilUsuario.apellido
        ).join(
            PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
        ).filter(
            or_(Usuario.sexo == 'M', Usuario.sexo == 'masculino')
        ).order_by(
            desc(Usuario.rating)
        ).limit(5).all()
        
        # 2. Top 5 femenino (una sola query con join)
        top_femenino = db.query(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Usuario.rating,
            Usuario.sexo,
            PerfilUsuario.nombre,
            PerfilUsuario.apellido
        ).join(
            PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
        ).filter(
            or_(Usuario.sexo == 'F', Usuario.sexo == 'femenino')
        ).order_by(
            desc(Usuario.rating)
        ).limit(5).all()
        
        # 3. Últimos 3 partidos del usuario (query optimizada)
        partidos_ids = db.query(PartidoJugador.id_partido).filter(
            PartidoJugador.id_usuario == user_id
        ).order_by(desc(PartidoJugador.id_partido)).limit(3).all()
        
        partidos_ids_list = [p[0] for p in partidos_ids]
        
        partidos_data = []
        if partidos_ids_list:
            # Obtener partidos con resultados en una sola query
            partidos = db.query(Partido).filter(
                Partido.id_partido.in_(partidos_ids_list)
            ).all()
            
            # Obtener resultados en batch
            resultados = db.query(ResultadoPartido).filter(
                ResultadoPartido.id_partido.in_(partidos_ids_list)
            ).all()
            resultados_dict = {r.id_partido: r for r in resultados}
            
            # Obtener historial de rating en batch
            historial = db.query(HistorialRating).filter(
                HistorialRating.id_partido.in_(partidos_ids_list),
                HistorialRating.id_usuario == user_id
            ).all()
            historial_dict = {h.id_partido: h for h in historial}
            
            # Obtener jugadores de los partidos en batch
            jugadores = db.query(PartidoJugador).filter(
                PartidoJugador.id_partido.in_(partidos_ids_list)
            ).all()
            jugadores_dict = {}
            for j in jugadores:
                if j.id_partido not in jugadores_dict:
                    jugadores_dict[j.id_partido] = []
                jugadores_dict[j.id_partido].append(j)
            
            # Construir respuesta
            for partido in partidos:
                resultado = resultados_dict.get(partido.id_partido)
                hist = historial_dict.get(partido.id_partido)
                jugs = jugadores_dict.get(partido.id_partido, [])
                
                # Determinar si fue victoria
                mi_equipo = None
                for j in jugs:
                    if j.id_usuario == user_id:
                        mi_equipo = j.equipo
                        break
                
                victoria = False
                if resultado and mi_equipo:
                    if mi_equipo == 1:
                        victoria = resultado.sets_eq1 > resultado.sets_eq2
                    else:
                        victoria = resultado.sets_eq2 > resultado.sets_eq1
                elif hist:
                    victoria = hist.delta > 0
                
                partidos_data.append({
                    "id_partido": partido.id_partido,
                    "fecha": partido.fecha.isoformat() if partido.fecha else None,
                    "victoria": victoria,
                    "delta": hist.delta if hist else 0
                })
        
        # 4. Delta de rating semanal
        hace_7_dias = datetime.now() - timedelta(days=7)
        delta_semanal = db.query(
            func.sum(HistorialRating.delta)
        ).filter(
            HistorialRating.id_usuario == user_id,
            HistorialRating.fecha >= hace_7_dias
        ).scalar() or 0
        
        # Formatear respuesta
        return {
            "top_masculino": [
                {
                    "id_usuario": u.id_usuario,
                    "nombre_usuario": u.nombre_usuario,
                    "nombre": u.nombre,
                    "apellido": u.apellido,
                    "rating": u.rating or 1200,
                    "sexo": u.sexo
                }
                for u in top_masculino
            ],
            "top_femenino": [
                {
                    "id_usuario": u.id_usuario,
                    "nombre_usuario": u.nombre_usuario,
                    "nombre": u.nombre,
                    "apellido": u.apellido,
                    "rating": u.rating or 1200,
                    "sexo": u.sexo
                }
                for u in top_femenino
            ],
            "ultimos_partidos": partidos_data,
            "delta_semanal": int(delta_semanal)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener datos del dashboard: {str(e)}"
        )
