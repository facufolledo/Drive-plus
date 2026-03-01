"""Migrar pareja 680 de temp 594 a usuario real 499"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

TEMP_ID = 594  # Sebastián Rodolzavich (temp nuevo T42)
REAL_ID = 499  # Sebastián Rodozaldovich (temp T38 con historial)
PAREJA_ID = 680

with engine.connect() as conn:
    print(f"=== Migrando pareja {PAREJA_ID} ===")
    
    # Verificar pareja actual
    pareja = conn.execute(text("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
               p1.nombre || ' ' || p1.apellido as j1,
               p2.nombre || ' ' || p2.apellido as j2
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios p1 ON p1.id_usuario = tp.jugador1_id
        LEFT JOIN perfil_usuarios p2 ON p2.id_usuario = tp.jugador2_id
        WHERE tp.id = :pid
    """), {"pid": PAREJA_ID}).fetchone()
    
    print(f"  Antes: {pareja[0]} - {pareja[3]} ({pareja[1]}) / {pareja[4]} ({pareja[2]})")
    
    # Actualizar jugador1_id
    conn.execute(text("""
        UPDATE torneos_parejas 
        SET jugador1_id = :real_id 
        WHERE id = :pid
    """), {"real_id": REAL_ID, "pid": PAREJA_ID})
    
    # Verificar después
    pareja_nueva = conn.execute(text("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
               p1.nombre || ' ' || p1.apellido as j1,
               p2.nombre || ' ' || p2.apellido as j2
        FROM torneos_parejas tp
        LEFT JOIN perfil_usuarios p1 ON p1.id_usuario = tp.jugador1_id
        LEFT JOIN perfil_usuarios p2 ON p2.id_usuario = tp.jugador2_id
        WHERE tp.id = :pid
    """), {"pid": PAREJA_ID}).fetchone()
    
    print(f"  Después: {pareja_nueva[0]} - {pareja_nueva[3]} ({pareja_nueva[1]}) / {pareja_nueva[4]} ({pareja_nueva[2]})")
    
    # Eliminar temp 594 si no tiene otras parejas
    otras_parejas = conn.execute(text("""
        SELECT COUNT(*) FROM torneos_parejas 
        WHERE jugador1_id = :tid OR jugador2_id = :tid
    """), {"tid": TEMP_ID}).fetchone()[0]
    
    if otras_parejas == 0:
        print(f"\n  Eliminando temp {TEMP_ID} (sin otras parejas)...")
        conn.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = :tid"), {"tid": TEMP_ID})
        conn.execute(text("DELETE FROM usuarios WHERE id_usuario = :tid"), {"tid": TEMP_ID})
        print(f"  ✅ Temp {TEMP_ID} eliminado")
    else:
        print(f"\n  ⚠️ Temp {TEMP_ID} tiene {otras_parejas} parejas, no se elimina")
    
    conn.commit()
    print("\n✅ Migración completada!")
