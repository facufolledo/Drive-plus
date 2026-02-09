"""
Actualizar ratings de principiantes con nuevos K-factors (ejecuta SQL directamente)
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

# SQL generado con los nuevos K-factors
sql_updates = """
BEGIN;

-- Actualizar historial_rating
UPDATE historial_rating SET rating_antes = 297, delta = 50.0, rating_despues = 347 WHERE id_usuario = 158 AND id_partido = 159;
UPDATE historial_rating SET rating_antes = 347, delta = 50.0, rating_despues = 397 WHERE id_usuario = 158 AND id_partido = 160;
UPDATE historial_rating SET rating_antes = 397, delta = 50.0, rating_despues = 447 WHERE id_usuario = 158 AND id_partido = 309;
UPDATE historial_rating SET rating_antes = 447, delta = -25.0, rating_despues = 422 WHERE id_usuario = 158 AND id_partido = 311;
UPDATE historial_rating SET rating_antes = 297, delta = 50.0, rating_despues = 347 WHERE id_usuario = 159 AND id_partido = 159;
UPDATE historial_rating SET rating_antes = 347, delta = 50.0, rating_despues = 397 WHERE id_usuario = 159 AND id_partido = 160;
UPDATE historial_rating SET rating_antes = 397, delta = 50.0, rating_despues = 447 WHERE id_usuario = 159 AND id_partido = 309;
UPDATE historial_rating SET rating_antes = 447, delta = -25.0, rating_despues = 422 WHERE id_usuario = 159 AND id_partido = 311;
UPDATE historial_rating SET rating_antes = 283, delta = -25.0, rating_despues = 258 WHERE id_usuario = 173 AND id_partido = 159;
UPDATE historial_rating SET rating_antes = 258, delta = -25.0, rating_despues = 233 WHERE id_usuario = 173 AND id_partido = 161;
UPDATE historial_rating SET rating_antes = 233, delta = 50.0, rating_despues = 283 WHERE id_usuario = 173 AND id_partido = 307;
UPDATE historial_rating SET rating_antes = 283, delta = 50.0, rating_despues = 333 WHERE id_usuario = 173 AND id_partido = 310;
UPDATE historial_rating SET rating_antes = 333, delta = 50.0, rating_despues = 383 WHERE id_usuario = 173 AND id_partido = 312;
UPDATE historial_rating SET rating_antes = 283, delta = -25.0, rating_despues = 258 WHERE id_usuario = 174 AND id_partido = 159;
UPDATE historial_rating SET rating_antes = 258, delta = -25.0, rating_despues = 233 WHERE id_usuario = 174 AND id_partido = 161;
UPDATE historial_rating SET rating_antes = 233, delta = 50.0, rating_despues = 283 WHERE id_usuario = 174 AND id_partido = 307;
UPDATE historial_rating SET rating_antes = 283, delta = 50.0, rating_despues = 333 WHERE id_usuario = 174 AND id_partido = 310;
UPDATE historial_rating SET rating_antes = 333, delta = 50.0, rating_despues = 383 WHERE id_usuario = 174 AND id_partido = 312;
UPDATE historial_rating SET rating_antes = 249, delta = -25.1, rating_despues = 224 WHERE id_usuario = 228 AND id_partido = 160;
UPDATE historial_rating SET rating_antes = 224, delta = 50.1, rating_despues = 274 WHERE id_usuario = 228 AND id_partido = 161;
UPDATE historial_rating SET rating_antes = 274, delta = -4.9, rating_despues = 269 WHERE id_usuario = 228 AND id_partido = 306;
UPDATE historial_rating SET rating_antes = 250, delta = -24.9, rating_despues = 225 WHERE id_usuario = 216 AND id_partido = 160;
UPDATE historial_rating SET rating_antes = 225, delta = 49.9, rating_despues = 275 WHERE id_usuario = 216 AND id_partido = 161;
UPDATE historial_rating SET rating_antes = 275, delta = -4.9, rating_despues = 270 WHERE id_usuario = 216 AND id_partido = 306;
UPDATE historial_rating SET rating_antes = 225, delta = -3.7, rating_despues = 221 WHERE id_usuario = 160 AND id_partido = 162;
UPDATE historial_rating SET rating_antes = 221, delta = -25.0, rating_despues = 196 WHERE id_usuario = 160 AND id_partido = 163;
UPDATE historial_rating SET rating_antes = 225, delta = -3.7, rating_despues = 221 WHERE id_usuario = 161 AND id_partido = 162;
UPDATE historial_rating SET rating_antes = 221, delta = -25.0, rating_despues = 196 WHERE id_usuario = 161 AND id_partido = 163;
UPDATE historial_rating SET rating_antes = 1125, delta = 3.0, rating_despues = 1128 WHERE id_usuario = 58 AND id_partido = 162;
UPDATE historial_rating SET rating_antes = 1128, delta = -16.3, rating_despues = 1112 WHERE id_usuario = 58 AND id_partido = 164;
UPDATE historial_rating SET rating_antes = 1112, delta = 3.4, rating_despues = 1115 WHERE id_usuario = 58 AND id_partido = 306;
UPDATE historial_rating SET rating_antes = 1115, delta = -16.2, rating_despues = 1099 WHERE id_usuario = 58 AND id_partido = 310;
UPDATE historial_rating SET rating_antes = 773, delta = 4.3, rating_despues = 777 WHERE id_usuario = 162 AND id_partido = 162;
UPDATE historial_rating SET rating_antes = 777, delta = -23.7, rating_despues = 753 WHERE id_usuario = 162 AND id_partido = 164;
UPDATE historial_rating SET rating_antes = 753, delta = 5.0, rating_despues = 758 WHERE id_usuario = 162 AND id_partido = 306;
UPDATE historial_rating SET rating_antes = 758, delta = -23.8, rating_despues = 734 WHERE id_usuario = 162 AND id_partido = 310;
UPDATE historial_rating SET rating_antes = 348, delta = 50.0, rating_despues = 398 WHERE id_usuario = 219 AND id_partido = 163;
UPDATE historial_rating SET rating_antes = 398, delta = 50.0, rating_despues = 448 WHERE id_usuario = 219 AND id_partido = 164;
UPDATE historial_rating SET rating_antes = 448, delta = -25.0, rating_despues = 423 WHERE id_usuario = 219 AND id_partido = 309;
UPDATE historial_rating SET rating_antes = 348, delta = 50.0, rating_despues = 398 WHERE id_usuario = 218 AND id_partido = 163;
UPDATE historial_rating SET rating_antes = 398, delta = 50.0, rating_despues = 448 WHERE id_usuario = 218 AND id_partido = 164;
UPDATE historial_rating SET rating_antes = 448, delta = -25.0, rating_despues = 423 WHERE id_usuario = 218 AND id_partido = 309;
UPDATE historial_rating SET rating_antes = 225, delta = -25.0, rating_despues = 200 WHERE id_usuario = 163 AND id_partido = 165;
UPDATE historial_rating SET rating_antes = 200, delta = -25.0, rating_despues = 175 WHERE id_usuario = 163 AND id_partido = 166;
UPDATE historial_rating SET rating_antes = 225, delta = -25.0, rating_despues = 200 WHERE id_usuario = 164 AND id_partido = 165;
UPDATE historial_rating SET rating_antes = 200, delta = -25.0, rating_despues = 175 WHERE id_usuario = 164 AND id_partido = 166;
UPDATE historial_rating SET rating_antes = 299, delta = 50.0, rating_despues = 349 WHERE id_usuario = 169 AND id_partido = 165;
UPDATE historial_rating SET rating_antes = 349, delta = 50.0, rating_despues = 399 WHERE id_usuario = 169 AND id_partido = 167;
UPDATE historial_rating SET rating_antes = 299, delta = 50.0, rating_despues = 349 WHERE id_usuario = 170 AND id_partido = 165;
UPDATE historial_rating SET rating_antes = 349, delta = 50.0, rating_despues = 399 WHERE id_usuario = 170 AND id_partido = 167;
UPDATE historial_rating SET rating_antes = 249, delta = 52.3, rating_despues = 301 WHERE id_usuario = 175 AND id_partido = 166;
UPDATE historial_rating SET rating_antes = 301, delta = -28.9, rating_despues = 272 WHERE id_usuario = 175 AND id_partido = 167;
UPDATE historial_rating SET rating_antes = 272, delta = -29.6, rating_despues = 242 WHERE id_usuario = 175 AND id_partido = 308;
UPDATE historial_rating SET rating_antes = 770, delta = 16.9, rating_despues = 787 WHERE id_usuario = 26 AND id_partido = 166;
UPDATE historial_rating SET rating_antes = 787, delta = -11.1, rating_despues = 776 WHERE id_usuario = 26 AND id_partido = 167;
UPDATE historial_rating SET rating_antes = 776, delta = -10.4, rating_despues = 766 WHERE id_usuario = 26 AND id_partido = 308;
UPDATE historial_rating SET rating_antes = 262, delta = 50.0, rating_despues = 312 WHERE id_usuario = 165 AND id_partido = 168;
UPDATE historial_rating SET rating_antes = 312, delta = -25.0, rating_despues = 287 WHERE id_usuario = 165 AND id_partido = 169;
UPDATE historial_rating SET rating_antes = 262, delta = 50.0, rating_despues = 312 WHERE id_usuario = 166 AND id_partido = 168;
UPDATE historial_rating SET rating_antes = 312, delta = -25.0, rating_despues = 287 WHERE id_usuario = 166 AND id_partido = 169;
UPDATE historial_rating SET rating_antes = 225, delta = -25.0, rating_despues = 200 WHERE id_usuario = 167 AND id_partido = 168;
UPDATE historial_rating SET rating_antes = 200, delta = -25.0, rating_despues = 175 WHERE id_usuario = 167 AND id_partido = 170;
UPDATE historial_rating SET rating_antes = 225, delta = -25.0, rating_despues = 200 WHERE id_usuario = 168 AND id_partido = 168;
UPDATE historial_rating SET rating_antes = 200, delta = -25.0, rating_despues = 175 WHERE id_usuario = 168 AND id_partido = 170;
UPDATE historial_rating SET rating_antes = 295, delta = 47.2, rating_despues = 342 WHERE id_usuario = 33 AND id_partido = 169;
UPDATE historial_rating SET rating_antes = 342, delta = 48.1, rating_despues = 390 WHERE id_usuario = 33 AND id_partido = 170;
UPDATE historial_rating SET rating_antes = 390, delta = -24.3, rating_despues = 366 WHERE id_usuario = 33 AND id_partido = 307;
UPDATE historial_rating SET rating_antes = 264, delta = 52.8, rating_despues = 317 WHERE id_usuario = 157 AND id_partido = 169;
UPDATE historial_rating SET rating_antes = 317, delta = 51.9, rating_despues = 369 WHERE id_usuario = 157 AND id_partido = 170;
UPDATE historial_rating SET rating_antes = 369, delta = -25.7, rating_despues = 343 WHERE id_usuario = 157 AND id_partido = 307;
UPDATE historial_rating SET rating_antes = 788, delta = -20.0, rating_despues = 768 WHERE id_usuario = 224 AND id_partido = 220;
UPDATE historial_rating SET rating_antes = 788, delta = -20.0, rating_despues = 768 WHERE id_usuario = 225 AND id_partido = 220;
UPDATE historial_rating SET rating_antes = 312, delta = 50.0, rating_despues = 362 WHERE id_usuario = 226 AND id_partido = 220;
UPDATE historial_rating SET rating_antes = 362, delta = 50.0, rating_despues = 412 WHERE id_usuario = 226 AND id_partido = 308;
UPDATE historial_rating SET rating_antes = 412, delta = 50.0, rating_despues = 462 WHERE id_usuario = 226 AND id_partido = 311;
UPDATE historial_rating SET rating_antes = 462, delta = -25.0, rating_despues = 437 WHERE id_usuario = 226 AND id_partido = 312;
UPDATE historial_rating SET rating_antes = 312, delta = 50.0, rating_despues = 362 WHERE id_usuario = 227 AND id_partido = 220;
UPDATE historial_rating SET rating_antes = 362, delta = 50.0, rating_despues = 412 WHERE id_usuario = 227 AND id_partido = 308;
UPDATE historial_rating SET rating_antes = 412, delta = 50.0, rating_despues = 462 WHERE id_usuario = 227 AND id_partido = 311;
UPDATE historial_rating SET rating_antes = 462, delta = -25.0, rating_despues = 437 WHERE id_usuario = 227 AND id_partido = 312;

-- Actualizar rating actual de usuarios
UPDATE usuarios SET rating = 422 WHERE id_usuario = 158;
UPDATE usuarios SET rating = 422 WHERE id_usuario = 159;
UPDATE usuarios SET rating = 383 WHERE id_usuario = 173;
UPDATE usuarios SET rating = 383 WHERE id_usuario = 174;
UPDATE usuarios SET rating = 269 WHERE id_usuario = 228;
UPDATE usuarios SET rating = 270 WHERE id_usuario = 216;
UPDATE usuarios SET rating = 196 WHERE id_usuario = 160;
UPDATE usuarios SET rating = 196 WHERE id_usuario = 161;
UPDATE usuarios SET rating = 1099 WHERE id_usuario = 58;
UPDATE usuarios SET rating = 734 WHERE id_usuario = 162;
UPDATE usuarios SET rating = 423 WHERE id_usuario = 219;
UPDATE usuarios SET rating = 423 WHERE id_usuario = 218;
UPDATE usuarios SET rating = 175 WHERE id_usuario = 163;
UPDATE usuarios SET rating = 175 WHERE id_usuario = 164;
UPDATE usuarios SET rating = 399 WHERE id_usuario = 169;
UPDATE usuarios SET rating = 399 WHERE id_usuario = 170;
UPDATE usuarios SET rating = 242 WHERE id_usuario = 175;
UPDATE usuarios SET rating = 766 WHERE id_usuario = 26;
UPDATE usuarios SET rating = 287 WHERE id_usuario = 165;
UPDATE usuarios SET rating = 287 WHERE id_usuario = 166;
UPDATE usuarios SET rating = 175 WHERE id_usuario = 167;
UPDATE usuarios SET rating = 175 WHERE id_usuario = 168;
UPDATE usuarios SET rating = 366 WHERE id_usuario = 33;
UPDATE usuarios SET rating = 343 WHERE id_usuario = 157;
UPDATE usuarios SET rating = 768 WHERE id_usuario = 224;
UPDATE usuarios SET rating = 768 WHERE id_usuario = 225;
UPDATE usuarios SET rating = 437 WHERE id_usuario = 226;
UPDATE usuarios SET rating = 437 WHERE id_usuario = 227;

COMMIT;
"""

try:
    with engine.connect() as conn:
        conn.execute(text(sql_updates))
        conn.commit()
        
        print("✅ Actualización completada exitosamente!")
        print("\n📊 Resumen:")
        print("   - 28 jugadores actualizados")
        print("   - 20 partidos recalculados")
        print("   - K-factor usado: 400 (principiantes)")
        print("\n🎯 Los jugadores principiantes ahora suben ~50 puntos por victoria")
        
except Exception as e:
    print(f"❌ Error al ejecutar actualización: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
