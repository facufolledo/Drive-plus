"""Recalcular partidos_jugados para TODOS los usuarios
Cuenta partidos confirmados donde el usuario participó (jugador1 o jugador2 en parejas)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Obtener todos los usuarios
    usuarios = conn.execute(text("""
        SELECT id_usuario, nombre_usuario FROM usuarios ORDER BY id_usuario
    """)).fetchall()
    
    print(f"Recalculando partidos_jugados para {len(usuarios)} usuarios...")
    
    actualizados = 0
    for uid, username in usuarios:
        # Contar partidos confirmados donde este usuario participó
        count = conn.execute(text("""
            SELECT COUNT(DISTINCT p.id_partido)
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            WHERE p.estado = 'confirmado'
              AND (tp1.jugador1_id = :uid OR tp1.jugador2_id = :uid 
                   OR tp2.jugador1_id = :uid OR tp2.jugador2_id = :uid)
        """), {"uid": uid}).fetchone()[0]
        
        # Actualizar
        conn.execute(text("""
            UPDATE usuarios SET partidos_jugados = :count WHERE id_usuario = :uid
        """), {"count": count, "uid": uid})
        
        actualizados += 1
        if actualizados % 50 == 0:
            print(f"  Procesados: {actualizados}/{len(usuarios)}")
    
    conn.commit()
    
    print(f"\n✅ {actualizados} usuarios actualizados")
    
    # Mostrar algunos ejemplos
    print("\n=== EJEMPLOS (usuarios con más partidos) ===")
    ejemplos = conn.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.partidos_jugados, u.rating
        FROM usuarios u
        WHERE u.partidos_jugados > 0
        ORDER BY u.partidos_jugados DESC
        LIMIT 10
    """)).fetchall()
    for e in ejemplos:
        print(f"  ID {e[0]}: {e[1]} -> {e[2]} partidos (rating: {e[3]})")
