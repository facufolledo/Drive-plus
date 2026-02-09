"""
Verificar que los ratings de principiantes se actualizaron correctamente
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

print("🔍 Verificando actualización de ratings de principiantes...")
print("=" * 60)

with engine.connect() as conn:
    # Obtener algunos jugadores principiantes y sus ratings
    query = text("""
        SELECT 
            u.id_usuario,
            pu.nombre,
            pu.apellido,
            u.rating,
            u.partidos_jugados,
            COUNT(hr.id_usuario) as registros_historial
        FROM usuarios u
        INNER JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
        LEFT JOIN historial_rating hr ON u.id_usuario = hr.id_usuario
        WHERE u.id_usuario IN (158, 159, 173, 174, 226, 227, 219, 218)
        GROUP BY u.id_usuario, pu.nombre, pu.apellido, u.rating, u.partidos_jugados
        ORDER BY u.rating DESC
    """)
    
    jugadores = conn.execute(query).fetchall()
    
    print("\n📊 Ratings actualizados de jugadores principiantes:")
    print("-" * 60)
    for j in jugadores:
        print(f"  {j.nombre} {j.apellido} (ID {j.id_usuario})")
        print(f"    Rating: {j.rating} | Partidos: {j.partidos_jugados} | Historial: {j.registros_historial}")
    
    # Verificar algunos deltas del historial
    query_historial = text("""
        SELECT 
            hr.id_usuario,
            pu.nombre,
            pu.apellido,
            hr.id_partido,
            hr.rating_antes,
            hr.delta,
            hr.rating_despues
        FROM historial_rating hr
        INNER JOIN perfil_usuarios pu ON hr.id_usuario = pu.id_usuario
        WHERE hr.id_usuario IN (158, 226)
        ORDER BY hr.id_usuario, hr.id_partido
    """)
    
    historial = conn.execute(query_historial).fetchall()
    
    print("\n📈 Historial de cambios (muestra):")
    print("-" * 60)
    for h in historial:
        signo = "+" if h.delta > 0 else ""
        print(f"  {h.nombre} {h.apellido} - Partido {h.id_partido}: {h.rating_antes} → {h.rating_despues} ({signo}{h.delta:.1f})")

print("\n✅ Verificación completada!")
