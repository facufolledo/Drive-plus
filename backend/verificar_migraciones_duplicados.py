"""
Verificar que las migraciones de duplicados se realizaron correctamente
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

# IDs que deben existir (destinos)
IDS_DESTINO = [57, 38, 210, 30, 81, 209]

# IDs que NO deben existir (orígenes eliminados)
IDS_ELIMINADOS = [225, 206, 129, 224, 125, 132]

print("🔍 Verificando migraciones de usuarios duplicados...")
print("=" * 80)

with engine.connect() as conn:
    print("\n✅ Verificando usuarios que DEBEN existir:")
    print("-" * 80)
    
    for id_usuario in IDS_DESTINO:
        query = text("""
            SELECT 
                u.id_usuario,
                pu.nombre,
                pu.apellido,
                u.email,
                u.rating,
                u.partidos_jugados,
                (SELECT COUNT(*) FROM torneos_parejas WHERE jugador1_id = u.id_usuario OR jugador2_id = u.id_usuario) as num_parejas,
                (SELECT COUNT(*) FROM historial_rating WHERE id_usuario = u.id_usuario) as num_historial
            FROM usuarios u
            INNER JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE u.id_usuario = :id
        """)
        
        result = conn.execute(query, {"id": id_usuario}).fetchone()
        
        if result:
            print(f"  ✓ ID {result.id_usuario}: {result.nombre} {result.apellido}")
            print(f"    Email: {result.email}")
            print(f"    Rating: {result.rating} | Partidos: {result.partidos_jugados}")
            print(f"    Parejas: {result.num_parejas} | Historial: {result.num_historial}")
        else:
            print(f"  ❌ ID {id_usuario}: NO ENCONTRADO (ERROR)")
    
    print("\n❌ Verificando usuarios que NO deben existir:")
    print("-" * 80)
    
    for id_usuario in IDS_ELIMINADOS:
        query = text("""
            SELECT id_usuario FROM usuarios WHERE id_usuario = :id
        """)
        
        result = conn.execute(query, {"id": id_usuario}).fetchone()
        
        if result:
            print(f"  ❌ ID {id_usuario}: AÚN EXISTE (ERROR)")
        else:
            print(f"  ✓ ID {id_usuario}: Eliminado correctamente")
    
    print("\n📊 Verificando casos pendientes:")
    print("-" * 80)
    
    # Esther Reyes (97, 98)
    query = text("""
        SELECT 
            u.id_usuario,
            pu.nombre,
            pu.apellido,
            u.email
        FROM usuarios u
        INNER JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
        WHERE u.id_usuario IN (97, 98)
        ORDER BY u.id_usuario
    """)
    
    esther = conn.execute(query).fetchall()
    print(f"  Esther Reyes: {len(esther)} cuentas encontradas")
    for e in esther:
        print(f"    - ID {e.id_usuario}: {e.email}")
    
    # Juan Pablo Romero (80, 124)
    query = text("""
        SELECT 
            u.id_usuario,
            pu.nombre,
            pu.apellido,
            u.email
        FROM usuarios u
        INNER JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
        WHERE u.id_usuario IN (80, 124)
        ORDER BY u.id_usuario
    """)
    
    juan = conn.execute(query).fetchall()
    print(f"  Juan Pablo Romero: {len(juan)} cuentas encontradas")
    for j in juan:
        print(f"    - ID {j.id_usuario}: {j.nombre} {j.apellido} ({j.email})")

print("\n✅ Verificación completada!")
