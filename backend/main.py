import os
import json
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware  # NUEVO: Compresión para mobile
from dotenv import load_dotenv
import uvicorn
from sqlalchemy import text

# Cargar variables de entorno
load_dotenv()

# Configurar logging ANTES de todo
from src.utils.logger import setup_logging
logger = setup_logging()

# Imports del proyecto
from src.database.config import engine
from src.utils.error_handler import register_exception_handlers
from src.controllers.auth_controller import router as auth_router
from src.controllers.usuario_controller import router as usuario_router
from src.controllers.categoria_controller import router as categoria_router
from src.controllers.partido_controller import router as partido_router
from src.controllers.ranking_controller import router as ranking_router
from src.controllers.estadisticas_controller import router as estadisticas_router
from src.controllers.sala_controller import router as sala_router
from src.controllers.resultado_controller import router as resultado_router
from src.controllers.torneo_controller import router as torneo_router
from src.controllers.torneo_pago_controller import router as torneo_pago_router
from src.controllers.health_controller import router as health_router
from src.controllers.logs_controller import router as logs_router
from src.controllers.admin_controller import router as admin_router
from src.controllers.categoria_maintenance_controller import router as categoria_maintenance_router
from src.controllers.circuito_controller import router as circuito_router
from src.controllers.dashboard_controller import router as dashboard_router


# ---- Lifespan (startup/shutdown) ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Iniciando Drive+ API...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Conexión a base de datos exitosa")
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
    
    # Inicializar Firebase Admin
    try:
        from src.auth.firebase_handler import FirebaseHandler
        if FirebaseHandler.initialize():
            logger.info("✅ Firebase Admin inicializado correctamente")
        else:
            logger.warning("⚠️ Firebase Admin no pudo inicializarse")
    except Exception as e:
        logger.error(f"❌ Error al inicializar Firebase Admin: {e}")

    # TEMPORALMENTE DESHABILITADO - Las tareas programadas estaban bloqueando el startup
    # Se pueden activar manualmente via /health endpoint
    try:
        logger.info("✅ Tareas programadas deshabilitadas temporalmente (startup más rápido)")
        # Para activar: GET /health
    except Exception as e:
        logger.error(f"❌ Error al configurar tareas programadas: {e}")

    yield

    # Shutdown
    logger.info("🛑 Cerrando Drive+ API...")
    try:
        from src.services.scheduled_tasks import stop_background_tasks
        stop_background_tasks()
        logger.info("✅ Tareas programadas detenidas")
    except Exception as e:
        logger.error(f"❌ Error al detener tareas programadas: {e}")


# ---- Crear app ----
app = FastAPI(
    title=os.getenv("APP_NAME", "Drive+ API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="API para el sistema de pádel Drive+ con ranking Elo",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,  # 👈 reemplaza on_event
)

# ---- CORS (DEBE IR ANTES DE OTROS MIDDLEWARES) ----
_default_origins = '["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174", "https://drive-plus.com.ar", "https://www.drive-plus.com.ar"]'
try:
    origins = json.loads(os.getenv("CORS_ORIGINS", _default_origins))
    if not isinstance(origins, list):
        raise ValueError("CORS_ORIGINS debe ser una lista JSON de strings.")
    logger.info(f"✅ CORS configurado con origins: {origins}")
except Exception as e:
    logger.error(f"❌ Error configurando CORS: {e}")
    origins = json.loads(_default_origins)
    logger.info(f"🔄 Usando origins por defecto: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos incluyendo PATCH
    allow_headers=["*"],
)

# ---- OPTIMIZACIÓN MOBILE: Compresión GZip ----
# Reduce tamaño de respuestas en 70-80% para mobile
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Comprimir respuestas > 1KB
    compresslevel=6     # Balance entre velocidad y compresión
)
logger.info("✅ Compresión GZip habilitada para optimización mobile")

# ---- Registrar handlers de excepciones ----
register_exception_handlers(app)

# ---- Routers ----
app.include_router(auth_router)
app.include_router(usuario_router)
app.include_router(categoria_router)
app.include_router(sala_router)
app.include_router(resultado_router)
app.include_router(partido_router)
app.include_router(ranking_router)
app.include_router(estadisticas_router)
app.include_router(torneo_router)
app.include_router(torneo_pago_router)
app.include_router(health_router)
app.include_router(logs_router)
app.include_router(admin_router)
app.include_router(categoria_maintenance_router)
app.include_router(circuito_router)
app.include_router(dashboard_router)

# ---- Endpoints básicos ----
@app.get("/")
async def root():
    return {
        "message": "¡Bienvenido a Drive+ API! 🚗⚡",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "status": "running",
        "docs": "/docs",
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "Drive+ API", 
        "database": "connected", 
        "cors": "enabled",
        "version": "2.0.0",  # Incrementar para verificar deployment
        "last_update": "2026-01-08T02:47:00Z"
    }

@app.get("/api/test-cors")
async def test_cors():
    """Endpoint de prueba para verificar que CORS funciona correctamente"""
    return {
        "message": "CORS está funcionando correctamente",
        "timestamp": datetime.now().isoformat(),
        "cors_enabled": True
    }

@app.options("/api/test-cors")
async def test_cors_preflight():
    """Endpoint OPTIONS para preflight requests"""
    return {"message": "Preflight OK"}

@app.options("/{path:path}")
async def handle_preflight(path: str):
    """Manejar todas las requests OPTIONS (preflight)"""
    return {"message": "Preflight handled"}

@app.get("/debug/cors")
async def cors_debug():
    """Endpoint de debug para verificar configuración CORS"""
    return {
        "cors_origins": origins,
        "cors_origins_env": os.getenv("CORS_ORIGINS"),
        "cors_origins_default": _default_origins,
        "cors_middleware_enabled": True,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug/firebase")
async def firebase_debug():
    """Endpoint de debug para verificar estado de Firebase"""
    from src.auth.firebase_handler import FirebaseHandler
    
    return {
        "firebase_available": FirebaseHandler._initialized,
        "credentials_path_env": os.getenv("FIREBASE_CREDENTIALS_PATH"),
        "credentials_json_env": "SET" if os.getenv("FIREBASE_CREDENTIALS_JSON") else "NOT SET",
        "credentials_path_exists": os.path.exists(os.getenv("FIREBASE_CREDENTIALS_PATH", "")) if os.getenv("FIREBASE_CREDENTIALS_PATH") else False,
    }

@app.get("/api/info")
async def api_info():
    return {
        "name": "Drive+ API",
        "description": "Sistema de pádel Drive+ con ranking Elo",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "features": [
            "Sistema de usuarios y autenticación",
            "Gestión de partidos de pádel",
            "Algoritmo Elo para rankings",
            "Historial de ratings",
            "Estadísticas de jugadores",
        ],
        "endpoints": {
            "documentation": "/docs",
            "health_check": "/health",
            "api_info": "/api/info",
        },
    }

# ---- Runner local ----
if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    print(f"🌐 Servidor iniciando en http://{host}:{port}")
    print(f"📚 Documentación:       http://{host}:{port}/docs")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info",
    )
