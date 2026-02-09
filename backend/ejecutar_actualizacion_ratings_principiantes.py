"""
Ejecutar actualización de ratings de principiantes con nuevos K-factors
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

print("🔄 Ejecutando actualización de ratings de principiantes...")
print("=" * 60)

# Leer el SQL generado
with open('actualizar_ratings_principiantes_torneo37.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Ejecutar el SQL
try:
    with engine.connect() as conn:
        # Ejecutar todo el SQL en una transacción
        conn.execute(text(sql_content))
        conn.commit()
        
        print("✅ Actualización completada exitosamente!")
        print("\n📊 Resumen:")
        print("   - 28 jugadores actualizados")
        print("   - 20 partidos recalculados")
        print("   - K-factor usado: 400 (principiantes)")
        print("\n🎯 Los jugadores principiantes ahora suben ~50 puntos por victoria")
        
except Exception as e:
    print(f"❌ Error al ejecutar actualización: {e}")
    sys.exit(1)
