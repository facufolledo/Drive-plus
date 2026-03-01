"""Eliminar usuarios temp que ya fueron migrados"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("Eliminando usuarios temp migrados (583, 593)...")

with engine.connect() as c:
    # Verificar que no estén en parejas
    parejas = c.execute(text("""
        SELECT id FROM torneos_parejas
        WHERE jugador1_id IN (583, 593) OR jugador2_id IN (583, 593)
    """)).fetchall()
    
    if parejas:
        print(f"⚠ Usuarios aún están en {len(parejas)} pareja(s), NO se eliminarán")
    else:
        # Eliminar perfiles
        c.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario IN (583, 593)"))
        # Eliminar usuarios
        result = c.execute(text("DELETE FROM usuarios WHERE id_usuario IN (583, 593)"))
        c.commit()
        print(f"✅ Eliminados {result.rowcount} usuarios temp")
