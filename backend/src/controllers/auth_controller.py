from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta
import os

from ..database.config import get_db
from ..models.driveplus_models import Usuario, PerfilUsuario, Categoria
from ..schemas.auth import UserLogin, UserRegister, Token, UserResponse, FirebaseAuthRequest
from ..auth.jwt_handler import JWTHandler
from ..auth.firebase_handler import FirebaseHandler
from ..auth.auth_utils import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# OAuth2 scheme para tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=Token)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario (solo email y contraseña)"""
    
    # Verificar si el email ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    try:
        # Crear hash de la contraseña
        hashed_password = JWTHandler.get_password_hash(user_data.password)
        
        # Generar nombre de usuario único basado en email
        email_base = user_data.email.split('@')[0]
        nombre_usuario = email_base
        contador = 1
        while db.query(Usuario).filter(Usuario.nombre_usuario == nombre_usuario).first():
            nombre_usuario = f"{email_base}{contador}"
            contador += 1
        
        # Crear usuario básico
        db_user = Usuario(
            nombre_usuario=nombre_usuario,
            email=user_data.email,
            password_hash=hashed_password,
            rating=1000,  # Rating por defecto
            partidos_jugados=0,
            sexo='M'  # Por defecto, se actualizará al completar perfil
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Crear token JWT para el usuario
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
        access_token = JWTHandler.create_access_token(
            data={"sub": str(db_user.id_usuario), "email": db_user.email},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Iniciar sesión (OAuth2 Password Flow).
    Swagger mandará form-data con fields: username, password.
    Usamos 'username' como email o nombre de usuario para autenticar.
    """
    # Buscar usuario por email o nombre de usuario
    user = db.query(Usuario).filter(
        (Usuario.email == form_data.username) | (Usuario.nombre_usuario == form_data.username)
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email/nombre de usuario o contraseña incorrectos"
        )

    # Verificar contraseña
    if not JWTHandler.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )

    # Crear token
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    access_token = JWTHandler.create_access_token(
        data={"sub": str(user.id_usuario), "email": user.email},
        expires_delta=access_token_expires
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds())
    )

# La función get_current_user ahora se importa desde auth_utils
# que soporta tanto JWT tradicional como tokens de Firebase

@router.get("/categorias")
async def get_categorias(db: Session = Depends(get_db)):
    """Obtener todas las categorías disponibles para el registro"""
    categorias = db.query(Categoria).order_by(Categoria.id_categoria.asc()).all()
    return [
        {
            "id_categoria": cat.id_categoria,
            "nombre": cat.nombre,
            "descripcion": cat.descripcion,
            "rating_min": cat.rating_min,
            "rating_max": cat.rating_max
        }
        for cat in categorias
    ]

@router.post("/firebase-auth", response_model=UserResponse)
async def firebase_auth(
    request: FirebaseAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Autenticar usuario con token de Firebase
    Verifica el token de Firebase y retorna información del usuario
    """
    try:
        # Validar token de Firebase
        firebase_payload = FirebaseHandler.verify_token(request.firebase_token)
        
        if not firebase_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de Firebase inválido o servicio no disponible",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        firebase_email = firebase_payload.get("firebase_email")
        
        if not firebase_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de Firebase inválido: email no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Buscar usuario por email
        user = db.query(Usuario).filter(Usuario.email == firebase_email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado. Por favor, completa tu perfil primero.",
            )
        
        # Obtener perfil del usuario
        perfil = db.query(PerfilUsuario).filter(PerfilUsuario.id_usuario == user.id_usuario).first()
        
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de usuario no encontrado",
            )
        
        return UserResponse(
            id_usuario=user.id_usuario,
            nombre_usuario=user.nombre_usuario,
            email=user.email,
            nombre=perfil.nombre,
            apellido=perfil.apellido,
            sexo=user.sexo,
            ciudad=perfil.ciudad,
            pais=perfil.pais,
            rating=user.rating,
            partidos_jugados=user.partidos_jugados,
            id_categoria=user.id_categoria,
            posicion_preferida=perfil.posicion_preferida,
            mano_dominante=perfil.mano_habil,
            foto_perfil=perfil.url_avatar,
            dni=perfil.dni,
            fecha_nacimiento=perfil.fecha_nacimiento.isoformat() if perfil.fecha_nacimiento else None,
            telefono=perfil.telefono,
            puede_crear_torneos=user.puede_crear_torneos or False,
            es_administrador=user.es_administrador or False
        )
    
    except HTTPException:
        # Re-lanzar HTTPException tal cual
        raise
    except Exception as e:
        # Capturar cualquier otro error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtener información del usuario actual (soporta JWT y Firebase tokens)"""
    
    # Obtener perfil del usuario
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
        telefono=perfil.telefono,
        puede_crear_torneos=current_user.puede_crear_torneos or False,
        es_administrador=current_user.es_administrador or False
    )
