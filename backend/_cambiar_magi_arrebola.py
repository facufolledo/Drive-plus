"""Cambiar pareja 636: sacar Mercado (512), poner Arrebola Jeremías (246)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

try:
    # Verificar estado actual
    antes = s.execute(text(
        "SELECT tp.id, tp.jugador1_id, tp.jugador2_id, p1.nombre, p1.apellido, p2.nombre, p2.apellido "
        "FROM torneos_parejas tp "
        "LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario "
        "LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario "
        "WHERE tp.id = 636"
    )).fetchone()
    print(f"ANTES: Pareja 636 = {antes[3]} {antes[4]} (ID {antes[1]}) + {antes[5]} {antes[6]} (ID {antes[2]})")

    # Actualizar jugador2 de Mercado (512) a Arrebola (246)
    s.execute(text(
        "UPDATE torneos_parejas SET jugador2_id = 246 WHERE id = 636"
    ))
    s.commit()

    # Verificar cambio
    despues = s.execute(text(
        "SELECT tp.id, tp.jugador1_id, tp.jugador2_id, p1.nombre, p1.apellido, p2.nombre, p2.apellido "
        "FROM torneos_parejas tp "
        "LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario "
        "LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario "
        "WHERE tp.id = 636"
    )).fetchone()
    print(f"DESPUÉS: Pareja 636 = {despues[3]} {despues[4]} (ID {despues[1]}) + {despues[5]} {despues[6]} (ID {despues[2]})")
    print("\n✅ Cambio realizado correctamente")

except Exception as e:
    print(f"❌ Error: {e}")
    s.rollback()
finally:
    s.close()
