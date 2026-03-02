"""
Controller optimizado para Dashboard - ULTRA RÁPIDO con 3 queries
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
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
    Endpoint ULTRA OPTIMIZADO - Solo 3 queries:
    1. Top 5 masculino + Top 5 femenino (1 query con UNION)
    2. Últimos 3 partidos con resultado (1 query con JOINs)
    3. Delta semanal (1 query simple)
    """
    try:
        user_id = current_user.id_usuario
        
        # QUERY 1: Top 5 masculino + Top 5 femenino en UNA SOLA QUERY
        # Normalizar sexo: M/masculino -> M, F/femenino -> F
        top_query = text("""
            (
                SELECT u.id_usuario, u.nombre_usuario, u.rating, u.sexo,
                       p.nombre, p.apellido, 'M' as sexo_norm
                FROM usuario u
                JOIN perfil_usuario p ON u.id_usuario = p.id_usuario
                WHERE UPPER(u.sexo) IN ('M', 'MASCULINO')
                ORDER BY u.rating DESC
                LIMIT 5
            )
            UNION ALL
            (
                SELECT u.id_usuario, u.nombre_usuario, u.rating, u.sexo,
                       p.nombre, p.apellido, 'F' as sexo_norm
                FROM usuario u
                JOIN perfil_usuario p ON u.id_usuario = p.id_usuario
                WHERE UPPER(u.sexo) IN ('F', 'FEMENINO')
                ORDER BY u.rating DESC
                LIMIT 5
            )
        """)
        
        top_result = db.execute(top_query).fetchall()
        
        top_masculino = []
        top_femenino = []
        
        for row in top_result:
            jugador = {
                "id_usuario": row[0],
                "nombre_usuario": row[1],
                "nombre": row[4],
                "apellido": row[5],
                "rating": row[2] or 1200,
                "sexo": row[3]
            }
            if row[6] == 'M':
                top_masculino.append(jugador)
            else:
                top_femenino.append(jugador)
        
        # QUERY 2: Últimos 3 partidos con resultado en UNA SOLA QUERY
        partidos_query = text("""
            SELECT 
                p.id_partido,
                p.fecha,
                r.sets_eq1,
                r.sets_eq2,
                pj.equipo,
                h.delta
            FROM partido_jugador pj
            JOIN partido p ON pj.id_partido = p.id_partido
            LEFT JOIN resultado_partido r ON p.id_partido = r.id_partido
            LEFT JOIN historial_rating h ON p.id_partido = h.id_partido AND h.id_usuario = :user_id
            WHERE pj.id_usuario = :user_id
            ORDER BY p.fecha DESC
            LIMIT 3
        """)
        
        partidos_result = db.execute(partidos_query, {"user_id": user_id}).fetchall()
        
        partidos_data = []
        for row in partidos_result:
            id_partido, fecha, sets_eq1, sets_eq2, equipo, delta = row
            
            # Determinar victoria
            victoria = False
            if sets_eq1 is not None and sets_eq2 is not None:
                if equipo == 1:
                    victoria = sets_eq1 > sets_eq2
                else:
                    victoria = sets_eq2 > sets_eq1
            elif delta is not None:
                victoria = delta > 0
            
            partidos_data.append({
                "id_partido": id_partido,
                "fecha": fecha.isoformat() if fecha else None,
                "victoria": victoria,
                "delta": delta or 0
            })
        
        # QUERY 3: Delta semanal (query simple y rápida)
        hace_7_dias = datetime.now() - timedelta(days=7)
        delta_query = text("""
            SELECT COALESCE(SUM(delta), 0) as total
            FROM historial_rating
            WHERE id_usuario = :user_id AND fecha >= :fecha_limite
        """)
        
        delta_result = db.execute(delta_query, {
            "user_id": user_id,
            "fecha_limite": hace_7_dias
        }).fetchone()
        
        delta_semanal = int(delta_result[0]) if delta_result else 0
        
        # Formatear respuesta
        return {
            "top_masculino": top_masculino,
            "top_femenino": top_femenino,
            "ultimos_partidos": partidos_data,
            "delta_semanal": delta_semanal
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener datos del dashboard: {str(e)}"
        )

