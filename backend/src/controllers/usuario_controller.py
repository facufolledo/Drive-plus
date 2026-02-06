from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..database.config import get_db
from ..models.driveplus_models import Usuario, PerfilUsuario, Categoria
from ..schemas.auth import UserResponse
from ..services.categoria_service import obtener_categoria_por_rating
from ..auth.auth_utils import get_current_user
from ..auth.firebase_handler import FirebaseHandler

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
security = HTTPBearer()


class CompletarPerfilRequest(BaseModel):
    nombre: str
    apellido: str
    dni: str
    fecha_nacimiento: str  # formato: YYYY-MM-DD
    genero: str  # 'masculino' o 'femenino'
    categoria_inicial: str  # '8va', '7ma', '6ta', '5ta', '4ta', 'Libre'
    mano_habil: Optional[str] = None  # 'derecha' o 'zurda'
    posicion_preferida: Optional[str] = None  # 'drive', 'reves', 'indiferente'
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    pais: Optional[str] = None


class ActualizarPerfilRequest(BaseModel):
    """Esquema para actualizar perfil de usuario"""
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    ciudad: Optional[str] = None
    pais: Optional[str] = None
    posicion_preferida: Optional[str] = None  # 'drive' o 'reves'
    mano_dominante: Optional[str] = None  # 'derecha' o 'zurda'
    foto_perfil: Optional[str] = None  # URL de la foto
    dni: Optional[str] = None
    fecha_nacimiento: Optional[str] = None  # formato: YYYY-MM-DD
    telefono: Optional[str] = None


@router.post("/completar-perfil", response_model=UserResponse)
async def completar_perfil(
    datos: CompletarPerfilRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Completar el perfil de un usuario que se registró con Firebase
    Si el usuario no existe, lo crea primero
    """
    try:
        # Verificar token de Firebase
        token = credentials.credentials
        firebase_payload = FirebaseHandler.verify_token(token)
        
        if not firebase_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de Firebase inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        firebase_email = firebase_payload.get("firebase_email")
        email_verified = firebase_payload.get("email_verified", False)
        
        if not firebase_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de Firebase inválido: email no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar que el email esté verificado
        if not email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Debes verificar tu correo electrónico antes de continuar. Revisa tu bandeja de entrada.",
            )
        
        # Mapear género a formato de base de datos
        sexo = 'M' if datos.genero == 'masculino' else 'F'
        
        # Buscar o crear usuario
        current_user = db.query(Usuario).filter(Usuario.email == firebase_email).first()
        
        if not current_user:
            # Crear nuevo usuario
            # Generar nombre de usuario único basado en email
            email_base = firebase_email.split('@')[0]
            nombre_usuario = email_base
            contador = 1
            while db.query(Usuario).filter(Usuario.nombre_usuario == nombre_usuario).first():
                nombre_usuario = f"{email_base}{contador}"
                contador += 1
            
            current_user = Usuario(
                nombre_usuario=nombre_usuario,
                email=firebase_email,
                password_hash="",  # No se usa para usuarios de Firebase
                rating=1000,  # Se actualizará según categoría
                partidos_jugados=0,
                sexo=sexo  # Asignar sexo al crear
            )
            db.add(current_user)
            db.flush()  # Para obtener el ID
        
        # Buscar categoría por nombre y sexo
        categoria = db.query(Categoria).filter(
            Categoria.nombre == datos.categoria_inicial,
            Categoria.sexo == datos.genero
        ).first()
        
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Categoría '{datos.categoria_inicial}' para género '{datos.genero}' no encontrada"
            )
        
        # Calcular rating inicial basado en la categoría
        rating_inicial = 1000  # Rating por defecto
        if categoria.rating_min is not None and categoria.rating_max is not None:
            rating_inicial = (categoria.rating_min + categoria.rating_max) // 2
        elif categoria.rating_min is not None:
            rating_inicial = categoria.rating_min + 50
        elif categoria.rating_max is not None:
            rating_inicial = categoria.rating_max - 50
        
        # Actualizar usuario
        current_user.sexo = sexo
        current_user.id_categoria = categoria.id_categoria
        current_user.rating = rating_inicial
        
        # Buscar o crear perfil
        perfil = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == current_user.id_usuario).first()
        
        if perfil:
            # Actualizar perfil existente
            perfil.nombre = datos.nombre
            perfil.apellido = datos.apellido
            perfil.dni = datos.dni
            perfil.fecha_nacimiento = datetime.strptime(datos.fecha_nacimiento, '%Y-%m-%d').date()
            perfil.ciudad = datos.ciudad or perfil.ciudad
            perfil.pais = datos.pais or perfil.pais or "Argentina"
            perfil.telefono = datos.telefono
            perfil.id_categoria_inicial = categoria.id_categoria
            perfil.mano_habil = datos.mano_habil
            perfil.posicion_preferida = datos.posicion_preferida
        else:
            # Crear nuevo perfil
            perfil = PerfilUsuario(
                id_usuario=current_user.id_usuario,
                nombre=datos.nombre,
                apellido=datos.apellido,
                dni=datos.dni,
                fecha_nacimiento=datetime.strptime(datos.fecha_nacimiento, '%Y-%m-%d').date(),
                ciudad=datos.ciudad,
                pais=datos.pais or "Argentina",
                telefono=datos.telefono,
                id_categoria_inicial=categoria.id_categoria,
                mano_habil=datos.mano_habil,
                posicion_preferida=datos.posicion_preferida
            )
            db.add(perfil)
        
        db.commit()
        db.refresh(current_user)
        db.refresh(perfil)
        
        return UserResponse(
            id_usuario=current_user.id_usuario,
            nombre_usuario=current_user.nombre_usuario,
            email=current_user.email,
            nombre=perfil.nombre,
            apellido=perfil.apellido,
            sexo=current_user.sexo,
            ciudad=perfil.ciudad,
            pais=perfil.pais,
            rating=current_user.rating,
            partidos_jugados=current_user.partidos_jugados,
            id_categoria=current_user.id_categoria,
            posicion_preferida=perfil.posicion_preferida,
            mano_dominante=perfil.mano_habil,
            foto_perfil=perfil.url_avatar,
            dni=perfil.dni,
            fecha_nacimiento=perfil.fecha_nacimiento.isoformat() if perfil.fecha_nacimiento else None,
            telefono=perfil.telefono
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de fecha inválido: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al completar perfil: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_usuario_actual(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener información del usuario actual
    """
    perfil = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == current_user.id_usuario).first()
    
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de usuario no encontrado"
        )
    
    return UserResponse(
        id_usuario=current_user.id_usuario,
        nombre_usuario=current_user.nombre_usuario,
        email=current_user.email,
        nombre=perfil.nombre,
        apellido=perfil.apellido,
        sexo=current_user.sexo,
        ciudad=perfil.ciudad,
        pais=perfil.pais,
        rating=current_user.rating,
        partidos_jugados=current_user.partidos_jugados,
        id_categoria=current_user.id_categoria,
        posicion_preferida=perfil.posicion_preferida,
        mano_dominante=perfil.mano_habil,
        foto_perfil=perfil.url_avatar,
        dni=perfil.dni,
        fecha_nacimiento=perfil.fecha_nacimiento.isoformat() if perfil.fecha_nacimiento else None,
        telefono=perfil.telefono
    )


@router.put("/perfil", response_model=UserResponse)
async def actualizar_perfil(
    datos: ActualizarPerfilRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar información del perfil del usuario actual
    """
    try:
        # Buscar perfil del usuario
        perfil = db.query(PerfilUsuario).filter(
            PerfilUsuario.id_usuario == current_user.id_usuario
        ).first()
        
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil no encontrado"
            )
        
        # Actualizar solo los campos que vienen en el request
        if datos.nombre is not None:
            perfil.nombre = datos.nombre
        
        if datos.apellido is not None:
            perfil.apellido = datos.apellido
        
        if datos.ciudad is not None:
            perfil.ciudad = datos.ciudad
        
        if datos.pais is not None:
            perfil.pais = datos.pais
        
        if datos.posicion_preferida is not None:
            # Validar que sea un valor válido
            if datos.posicion_preferida not in ['drive', 'reves', 'indiferente']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="posicion_preferida debe ser 'drive', 'reves' o 'indiferente'"
                )
            perfil.posicion_preferida = datos.posicion_preferida
        
        if datos.mano_dominante is not None:
            # Validar que sea un valor válido
            if datos.mano_dominante not in ['derecha', 'zurda']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="mano_dominante debe ser 'derecha' o 'zurda'"
                )
            perfil.mano_habil = datos.mano_dominante
        
        if datos.foto_perfil is not None:
            perfil.url_avatar = datos.foto_perfil
        
        if datos.dni is not None:
            perfil.dni = datos.dni
        
        if datos.fecha_nacimiento is not None:
            try:
                perfil.fecha_nacimiento = datetime.strptime(datos.fecha_nacimiento, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de fecha inválido. Use YYYY-MM-DD"
                )
        
        if datos.telefono is not None:
            perfil.telefono = datos.telefono
        
        db.commit()
        db.refresh(perfil)
        db.refresh(current_user)
        
        return UserResponse(
            id_usuario=current_user.id_usuario,
            nombre_usuario=current_user.nombre_usuario,
            email=current_user.email,
            nombre=perfil.nombre,
            apellido=perfil.apellido,
            sexo=current_user.sexo,
            ciudad=perfil.ciudad,
            pais=perfil.pais,
            rating=current_user.rating,
            partidos_jugados=current_user.partidos_jugados,
            id_categoria=current_user.id_categoria,
            posicion_preferida=perfil.posicion_preferida,
            mano_dominante=perfil.mano_habil,
            foto_perfil=perfil.url_avatar,
            dni=perfil.dni,
            fecha_nacimiento=perfil.fecha_nacimiento.isoformat() if perfil.fecha_nacimiento else None,
            telefono=perfil.telefono
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar perfil: {str(e)}"
        )


class FCMTokenRequest(BaseModel):
    fcm_token: str


@router.post("/fcm-token")
async def registrar_fcm_token(
    datos: FCMTokenRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registrar o actualizar el token FCM del usuario para notificaciones push
    """
    try:
        current_user.fcm_token = datos.fcm_token
        db.commit()
        
        return {
            "success": True,
            "message": "Token FCM registrado exitosamente"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar token FCM: {str(e)}"
        )


@router.get("/buscar")
async def buscar_usuarios(
    q: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Busca usuarios por nombre, apellido o nombre de usuario (OPTIMIZADO)
    """
    if not q or len(q) < 2:
        return []
    
    query_lower = f"%{q.lower()}%"
    
    # OPTIMIZACIÓN: Query única con joins incluyendo categoría
    resultados = db.query(
        Usuario.id_usuario,
        Usuario.nombre_usuario,
        Usuario.rating,
        Usuario.partidos_jugados,
        Usuario.id_categoria,
        PerfilUsuario.nombre,
        PerfilUsuario.apellido,
        PerfilUsuario.ciudad,
        PerfilUsuario.url_avatar,
        Categoria.nombre.label('categoria_nombre')
    ).join(
        PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
    ).outerjoin(
        Categoria, Usuario.id_categoria == Categoria.id_categoria
    ).filter(
        (PerfilUsuario.nombre.ilike(query_lower)) | 
        (PerfilUsuario.apellido.ilike(query_lower)) |
        (Usuario.nombre_usuario.ilike(query_lower))
    ).limit(limit).all()
    
    # Procesar resultados en memoria
    resultado = []
    for row in resultados:
        resultado.append({
            "id_usuario": row.id_usuario,
            "nombre_usuario": row.nombre_usuario,
            "nombre": row.nombre,
            "apellido": row.apellido,
            "nombre_completo": f"{row.nombre} {row.apellido}",
            "rating": row.rating or 1200,
            "partidos_jugados": row.partidos_jugados or 0,
            "categoria": row.categoria_nombre,
            "ciudad": row.ciudad,
            "foto_perfil": row.url_avatar
        })
    
    return resultado


@router.get("/@{username}/perfil")
async def obtener_perfil_por_username(
    username: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene el perfil público de un usuario por su username (OPTIMIZADO)
    URL amigable: /usuarios/@facufolledo/perfil
    """
    # OPTIMIZACIÓN: Query única con joins
    resultado = db.query(
        Usuario.id_usuario,
        Usuario.nombre_usuario,
        Usuario.sexo,
        Usuario.rating,
        Usuario.partidos_jugados,
        Usuario.id_categoria,
        PerfilUsuario.nombre,
        PerfilUsuario.apellido,
        PerfilUsuario.ciudad,
        PerfilUsuario.pais,
        PerfilUsuario.posicion_preferida,
        PerfilUsuario.mano_habil,
        PerfilUsuario.url_avatar,
        Categoria.nombre.label('categoria_nombre')
    ).join(
        PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
    ).outerjoin(
        Categoria, Usuario.id_categoria == Categoria.id_categoria
    ).filter(
        Usuario.nombre_usuario == username
    ).first()
    
    if not resultado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "id_usuario": resultado.id_usuario,
        "nombre_usuario": resultado.nombre_usuario,
        "nombre": resultado.nombre,
        "apellido": resultado.apellido,
        "nombre_completo": f"{resultado.nombre} {resultado.apellido}",
        "sexo": resultado.sexo,
        "ciudad": resultado.ciudad,
        "pais": resultado.pais,
        "rating": resultado.rating or 1200,
        "partidos_jugados": resultado.partidos_jugados or 0,
        "categoria": resultado.categoria_nombre,
        "categoria_id": resultado.id_categoria,
        "posicion_preferida": resultado.posicion_preferida,
        "mano_dominante": resultado.mano_habil,
        "foto_perfil": resultado.url_avatar
    }


@router.get("/{user_id}/perfil")
async def obtener_perfil_publico(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene el perfil público de un usuario por ID (OPTIMIZADO)
    """
    # OPTIMIZACIÓN: Query única con joins
    # IMPORTANTE: Usar outerjoin para perfil_usuario porque algunos usuarios pueden no tener perfil
    resultado = db.query(
        Usuario.id_usuario,
        Usuario.nombre_usuario,
        Usuario.sexo,
        Usuario.rating,
        Usuario.partidos_jugados,
        Usuario.id_categoria,
        PerfilUsuario.nombre,
        PerfilUsuario.apellido,
        PerfilUsuario.ciudad,
        PerfilUsuario.pais,
        PerfilUsuario.posicion_preferida,
        PerfilUsuario.mano_habil,
        PerfilUsuario.url_avatar,
        Categoria.nombre.label('categoria_nombre')
    ).outerjoin(
        PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
    ).outerjoin(
        Categoria, Usuario.id_categoria == Categoria.id_categoria
    ).filter(
        Usuario.id_usuario == user_id
    ).first()
    
    if not resultado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Manejar caso donde no hay perfil (nombre y apellido pueden ser None)
    nombre = resultado.nombre or "Usuario"
    apellido = resultado.apellido or ""
    nombre_completo = f"{nombre} {apellido}".strip()
    
    return {
        "id_usuario": resultado.id_usuario,
        "nombre_usuario": resultado.nombre_usuario,
        "nombre": nombre,
        "apellido": apellido,
        "nombre_completo": nombre_completo,
        "sexo": resultado.sexo,
        "ciudad": resultado.ciudad or "",
        "pais": resultado.pais or "Argentina",
        "rating": resultado.rating or 1200,
        "partidos_jugados": resultado.partidos_jugados or 0,
        "categoria": resultado.categoria_nombre,
        "categoria_id": resultado.id_categoria,
        "posicion_preferida": resultado.posicion_preferida,
        "mano_dominante": resultado.mano_habil,
        "foto_perfil": resultado.url_avatar
    }


@router.get("/{user_id}/estadisticas")
async def obtener_estadisticas_usuario(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas públicas de un usuario (OPTIMIZADO)
    """
    from ..models.driveplus_models import Partido, PartidoJugador, ResultadoPartido
    from sqlalchemy import and_
    
    usuario = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # OPTIMIZACIÓN: Obtener partidos del usuario
    partidos_jugador = db.query(PartidoJugador).filter(
        PartidoJugador.id_usuario == user_id
    ).all()
    
    if not partidos_jugador:
        return {
            "id_usuario": user_id,
            "partidos_jugados": 0,
            "victorias": 0,
            "derrotas": 0,
            "winrate": 0,
            "rating": usuario.rating or 1200
        }
    
    partidos_ids = [pj.id_partido for pj in partidos_jugador]
    
    # OPTIMIZACIÓN: Obtener TODOS los resultados en una sola query (batch)
    resultados = db.query(ResultadoPartido).filter(
        ResultadoPartido.id_partido.in_(partidos_ids),
        ResultadoPartido.confirmado == True
    ).all()
    
    # Crear diccionario para acceso rápido
    resultados_dict = {r.id_partido: r for r in resultados}
    
    # Contar victorias y derrotas (procesamiento en memoria)
    victorias = 0
    derrotas = 0
    
    for pj in partidos_jugador:
        resultado = resultados_dict.get(pj.id_partido)
        
        if resultado:
            if pj.equipo == 1:
                if resultado.sets_eq1 > resultado.sets_eq2:
                    victorias += 1
                else:
                    derrotas += 1
            else:
                if resultado.sets_eq2 > resultado.sets_eq1:
                    victorias += 1
                else:
                    derrotas += 1
    
    total = victorias + derrotas
    winrate = round((victorias / total * 100), 1) if total > 0 else 0
    
    return {
        "id_usuario": user_id,
        "partidos_jugados": total,
        "victorias": victorias,
        "derrotas": derrotas,
        "winrate": winrate,
        "rating": usuario.rating or 1200
    }


# ============================================
# ENDPOINTS ADICIONALES PARA PERFIL PÚBLICO
# ============================================

@router.get("/perfil-publico/{username}")
async def get_perfil_publico_por_username(
    username: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene el perfil público de un usuario por su username (OPTIMIZADO)
    Endpoint público - no requiere autenticación
    """
    try:
        # Limpiar el username de espacios y caracteres especiales
        username = username.strip().lower()
        
        # OPTIMIZACIÓN: Query única con joins (case insensitive)
        # IMPORTANTE: Usar outerjoin para perfil_usuario porque algunos usuarios pueden no tener perfil
        resultado = db.query(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Usuario.sexo,
            Usuario.rating,
            Usuario.partidos_jugados,
            Usuario.id_categoria,
            Usuario.creado_en,
            PerfilUsuario.nombre,
            PerfilUsuario.apellido,
            PerfilUsuario.ciudad,
            PerfilUsuario.pais,
            PerfilUsuario.posicion_preferida,
            PerfilUsuario.mano_habil,
            PerfilUsuario.url_avatar,
            Categoria.nombre.label('categoria_nombre')
        ).outerjoin(
            PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
        ).outerjoin(
            Categoria, Usuario.id_categoria == Categoria.id_categoria
        ).filter(
            Usuario.nombre_usuario.ilike(username)
        ).first()
        
        if not resultado:
            raise HTTPException(
                status_code=404, 
                detail=f"Usuario '{username}' no encontrado"
            )
        
        # Manejar caso donde no hay perfil (nombre y apellido pueden ser None)
        nombre = resultado.nombre or "Usuario"
        apellido = resultado.apellido or ""
        nombre_completo = f"{nombre} {apellido}".strip()
        
        # Si no tiene categoría asignada, derivarla del rating
        categoria_nombre = resultado.categoria_nombre
        if not categoria_nombre:
            rating = resultado.rating or 1200
            sexo = resultado.sexo or "M"
            sexo_str = "masculino" if str(sexo).upper() in ("M", "MASCULINO") else "femenino"
            cat = obtener_categoria_por_rating(db, rating, sexo_str)
            if cat:
                categoria_nombre = cat.nombre
        
        return {
            "id_usuario": resultado.id_usuario,
            "nombre_usuario": resultado.nombre_usuario,
            "nombre": nombre,
            "apellido": apellido,
            "nombre_completo": nombre_completo,
            "sexo": resultado.sexo,
            "ciudad": resultado.ciudad or "",
            "pais": resultado.pais or "Argentina",
            "rating": resultado.rating or 1200,
            "partidos_jugados": resultado.partidos_jugados or 0,
            "categoria": categoria_nombre,
            "categoria_id": resultado.id_categoria,
            "posicion_preferida": resultado.posicion_preferida,
            "mano_dominante": resultado.mano_habil,
            "foto_perfil": resultado.url_avatar,
            "fecha_registro": resultado.creado_en.isoformat() if resultado.creado_en else None,
            "activo": True  # Asumimos activo por defecto
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en perfil público: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno del servidor"
        )


@router.get("/buscar-publico")
async def buscar_usuarios_publico(
    q: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Búsqueda pública de usuarios por nombre, apellido o username (OPTIMIZADO)
    Endpoint público - no requiere autenticación
    """
    try:
        if not q or len(q.strip()) < 2:
            return []
        
        search_term = f"%{q.strip().lower()}%"
        
        # OPTIMIZACIÓN: Query única con joins incluyendo categoría
        # IMPORTANTE: Usar outerjoin para perfil_usuario porque algunos usuarios pueden no tener perfil
        resultados = db.query(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Usuario.rating,
            Usuario.partidos_jugados,
            Usuario.id_categoria,
            Usuario.sexo,
            Usuario.creado_en,
            PerfilUsuario.nombre,
            PerfilUsuario.apellido,
            PerfilUsuario.ciudad,
            PerfilUsuario.url_avatar,
            Categoria.nombre.label('categoria_nombre')
        ).outerjoin(
            PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
        ).outerjoin(
            Categoria, Usuario.id_categoria == Categoria.id_categoria
        ).filter(
            or_(
                Usuario.nombre_usuario.ilike(search_term),
                PerfilUsuario.nombre.ilike(search_term),
                PerfilUsuario.apellido.ilike(search_term)
            )
        ).limit(limit).all()
        
        # Procesar resultados en memoria
        resultado = []
        for row in resultados:
            nombre = row.nombre or "Usuario"
            apellido = row.apellido or ""
            # Si no tiene categoría asignada, derivarla del rating
            cat_nombre = row.categoria_nombre
            if not cat_nombre:
                rating = row.rating or 1200
                sexo = row.sexo or "M"
                sexo_str = "masculino" if str(sexo).upper() in ("M", "MASCULINO") else "femenino"
                cat = obtener_categoria_por_rating(db, rating, sexo_str)
                if cat:
                    cat_nombre = cat.nombre
            resultado.append({
                "id_usuario": row.id_usuario,
                "nombre_usuario": row.nombre_usuario,
                "nombre": nombre,
                "apellido": apellido,
                "nombre_completo": f"{nombre} {apellido}".strip(),
                "rating": row.rating or 1200,
                "partidos_jugados": row.partidos_jugados or 0,
                "categoria": cat_nombre,
                "ciudad": row.ciudad or "",
                "foto_perfil": row.url_avatar,
                "fecha_registro": row.creado_en.isoformat() if row.creado_en else None
            })
        
        return resultado
        
    except Exception as e:
        print(f"Error en búsqueda pública: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


@router.get("/debug-busqueda")
async def debug_busqueda(db: Session = Depends(get_db)):
    """
    Endpoint temporal de debug para verificar datos en producción
    """
    try:
        from sqlalchemy import or_
        
        # Contar usuarios
        total_usuarios = db.query(Usuario).count()
        
        # Contar perfiles
        total_perfiles = db.query(PerfilUsuario).count()
        
        # Primeros 5 usuarios
        usuarios = db.query(Usuario).limit(5).all()
        usuarios_data = [
            {
                "id": u.id_usuario,
                "username": u.nombre_usuario,
                "email": u.email
            }
            for u in usuarios
        ]
        
        # Primeros 5 perfiles
        perfiles = db.query(PerfilUsuario).limit(5).all()
        perfiles_data = [
            {
                "id_usuario": p.id_usuario,
                "nombre": p.nombre,
                "apellido": p.apellido
            }
            for p in perfiles
        ]
        
        # Test búsqueda con "fac"
        search_term = "%fac%"
        resultados_join = db.query(Usuario, PerfilUsuario).outerjoin(
            PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario
        ).filter(
            or_(
                Usuario.nombre_usuario.ilike(search_term),
                PerfilUsuario.nombre.ilike(search_term),
                PerfilUsuario.apellido.ilike(search_term)
            )
        ).limit(5).all()
        
        join_data = []
        for usuario, perfil in resultados_join:
            join_data.append({
                "usuario": usuario.nombre_usuario if usuario else None,
                "perfil": f"{perfil.nombre} {perfil.apellido}" if perfil else "SIN PERFIL"
            })
        
        return {
            "total_usuarios": total_usuarios,
            "total_perfiles": total_perfiles,
            "primeros_usuarios": usuarios_data,
            "primeros_perfiles": perfiles_data,
            "test_busqueda_fac": {
                "resultados": len(resultados_join),
                "datos": join_data
            }
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
