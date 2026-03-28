import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.torneo_fixture_global_service import TorneoFixtureGlobalService
from src.models.torneo_models import TorneoCategoria, Torneo

load_dotenv('.env.production')

# Configurar conexión
DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

print("=" * 80)
print("GENERAR FIXTURE PRINCIPIANTE - TORNEO 46 (USANDO SERVICIO)")
print("=" * 80)

db = SessionLocal()

try:
    # Obtener categoría Principiante
    categoria = db.query(TorneoCategoria).filter(
        TorneoCategoria.torneo_id == 46,
        TorneoCategoria.nombre == 'Principiante'
    ).first()
    
    if not categoria:
        print("❌ Categoría Principiante no encontrada")
        db.close()
        exit(1)
    
    print(f"✅ Categoría Principiante ID: {categoria.id}")
    
    # Obtener ID del organizador del torneo
    torneo = db.query(Torneo).filter(Torneo.id == 46).first()
    if not torneo:
        print("❌ Torneo 46 no encontrado")
        db.close()
        exit(1)
    
    user_id = torneo.creado_por
    print(f"✅ Organizador ID: {user_id}")
    
    print("\n" + "=" * 80)
    print("GENERANDO FIXTURE CON SERVICIO")
    print("=" * 80)
    
    # Generar fixture usando el servicio
    resultado = TorneoFixtureGlobalService.generar_fixture_completo(
        db=db,
        torneo_id=46,
        user_id=user_id,
        categoria_id=categoria.id
    )
    
    print("\n" + "=" * 80)
    print("RESULTADO")
    print("=" * 80)
    print(f"✅ Partidos generados: {resultado['partidos_generados']}")
    print(f"⚠️  Partidos no programados: {resultado['partidos_no_programados']}")
    print(f"📊 Zonas procesadas: {resultado['zonas_procesadas']}")
    
    if resultado['partidos_sin_programar']:
        print(f"\n⚠️  PARTIDOS SIN PROGRAMAR:")
        for p in resultado['partidos_sin_programar']:
            print(f"   - Partido {p.get('id', 'N/A')}: {p.get('motivo', 'Sin motivo')}")
    
    print("\n✅ Fixture generado exitosamente")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
