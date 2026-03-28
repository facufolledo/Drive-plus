import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.torneo_fixture_global_service import TorneoFixtureGlobalService
from src.models.torneo_models import TorneoCategoria, Torneo

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')

print("=" * 80)
print("REGENERAR FIXTURE PRINCIPIANTE CON ZONAS CORRECTAS - TORNEO 46")
print("=" * 80)

# Paso 1: Eliminar partidos actuales de Principiante
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

try:
    print("\n1️⃣ Eliminando partidos actuales de Principiante...")
    
    cur.execute("""
        DELETE FROM partidos
        WHERE id_torneo = 46
        AND categoria_id = 125
        AND fase = 'zona'
    """)
    
    partidos_eliminados = cur.rowcount
    conn.commit()
    
    print(f"   ✅ {partidos_eliminados} partidos eliminados")
    
    # Paso 2: Eliminar zonas actuales
    print("\n2️⃣ Eliminando zonas actuales...")
    
    cur.execute("""
        DELETE FROM torneo_zonas
        WHERE torneo_id = 46
        AND categoria_id = 125
    """)
    
    zonas_eliminadas = cur.rowcount
    conn.commit()
    
    print(f"   ✅ {zonas_eliminadas} zonas eliminadas")
    
    # Paso 3: Crear zonas con distribución correcta
    print("\n3️⃣ Creando zonas con distribución correcta...")
    
    zonas_config = [
        {
            'nombre': 'Zona A',
            'parejas': [1041, 1042, 1048]  # Jatuff/Alcazar, Aballay/Ríos, Ludueña/Apostolo
        },
        {
            'nombre': 'Zona B',
            'parejas': [1043, 1044, 1045]  # Velázquez/Zurita, Córdoba/Paez, Sotomayor/Diaz
        },
        {
            'nombre': 'Zona C',
            'parejas': [1046, 1047, 1049]  # Morales/Vera, Vera/Calderón, Agostini/Paez
        },
        {
            'nombre': 'Zona D',
            'parejas': [1050, 1051, 1052]  # Villalba/Alvarado, Toledo/Barrionuevo, Molina/Dávila
        }
    ]
    
    for idx, zona_config in enumerate(zonas_config, 1):
        cur.execute("""
            INSERT INTO torneo_zonas (torneo_id, nombre, categoria_id, numero_orden)
            VALUES (46, %s, 125, %s)
            RETURNING id
        """, (zona_config['nombre'], idx))
        
        zona_id = cur.fetchone()['id']
        
        # Obtener nombres de parejas
        parejas_nombres = []
        for pareja_id in zona_config['parejas']:
            cur.execute("""
                SELECT 
                    pu1.nombre || ' ' || pu1.apellido as j1,
                    pu2.nombre || ' ' || pu2.apellido as j2
                FROM torneos_parejas tp
                JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
                JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
                WHERE tp.id = %s
            """, (pareja_id,))
            
            pareja = cur.fetchone()
            if pareja:
                parejas_nombres.append(f"P{pareja_id}: {pareja['j1']}/{pareja['j2']}")
        
        print(f"\n   ✅ {zona_config['nombre']} (ID: {zona_id})")
        for nombre in parejas_nombres:
            print(f"      - {nombre}")
    
    conn.commit()
    print(f"\n   ✅ Zonas creadas (partidos se generarán con el servicio)")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    cur.close()
    conn.close()
    exit(1)

cur.close()
conn.close()

# Paso 4: Generar horarios con el servicio
print("\n4️⃣ Generando horarios con el servicio...")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    categoria = db.query(TorneoCategoria).filter(
        TorneoCategoria.torneo_id == 46,
        TorneoCategoria.nombre == 'Principiante'
    ).first()
    
    torneo = db.query(Torneo).filter(Torneo.id == 46).first()
    user_id = torneo.creado_por
    
    # Generar fixture usando el servicio
    resultado = TorneoFixtureGlobalService.generar_fixture_completo(
        db=db,
        torneo_id=46,
        user_id=user_id,
        categoria_id=categoria.id
    )
    
    print("\n" + "=" * 80)
    print("✅ FIXTURE REGENERADO EXITOSAMENTE")
    print("=" * 80)
    print(f"  - Partidos programados: {resultado['partidos_generados']}")
    print(f"  - Partidos sin programar: {resultado['partidos_no_programados']}")
    print(f"  - Zonas procesadas: {resultado['zonas_procesadas']}")
    
    print("\n📋 ZONA A (REQUERIDA):")
    print("  - P1041: Jatuff/Alcazar")
    print("  - P1042: Aballay/Ríos")
    print("  - P1048: Ludueña/Apostolo")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
