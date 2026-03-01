"""Limpiar duplicados globales según instrucciones del usuario"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# Duplicados a procesar
duplicados = [
    # (temp_id, real_id, accion, descripcion)
    (539, 6, "eliminar", "Matías Castelli - eliminar temp 539"),
    (505, 506, "eliminar", "Joaquín Mercado - eliminar 505, mantener 506"),
    (541, 560, "migrar", "Facundo Rodríguez - migrar temp 541 a real 560"),
    (532, 243, "eliminar", "Álvaro Ferreyra - eliminar temp 532"),
]

with engine.connect() as conn:
    print("=== LIMPIEZA DE DUPLICADOS ===\n")
    
    for temp_id, real_id, accion, desc in duplicados:
        print(f"\n{desc}")
        
        # Verificar parejas del temp
        parejas_temp = conn.execute(text("""
            SELECT tp.id, tp.torneo_id,
                   p1.nombre || ' ' || p1.apellido as j1,
                   p2.nombre || ' ' || p2.apellido as j2
            FROM torneos_parejas tp
            LEFT JOIN perfil_usuarios p1 ON p1.id_usuario = tp.jugador1_id
            LEFT JOIN perfil_usuarios p2 ON p2.id_usuario = tp.jugador2_id
            WHERE tp.jugador1_id = :tid OR tp.jugador2_id = :tid
        """), {"tid": temp_id}).fetchall()
        
        if parejas_temp:
            print(f"  ⚠️ Usuario {temp_id} tiene {len(parejas_temp)} parejas:")
            for p in parejas_temp:
                print(f"    - Pareja {p[0]} en T{p[1]}: {p[2]} / {p[3]}")
            
            if accion == "migrar":
                print(f"  → Migrando parejas de {temp_id} a {real_id}...")
                # Migrar jugador1_id
                conn.execute(text("""
                    UPDATE torneos_parejas 
                    SET jugador1_id = :real_id 
                    WHERE jugador1_id = :temp_id
                """), {"real_id": real_id, "temp_id": temp_id})
                # Migrar jugador2_id
                conn.execute(text("""
                    UPDATE torneos_parejas 
                    SET jugador2_id = :real_id 
                    WHERE jugador2_id = :temp_id
                """), {"real_id": real_id, "temp_id": temp_id})
                print(f"  ✅ Parejas migradas")
            else:
                print(f"  ⚠️ NO SE PUEDE ELIMINAR - tiene parejas activas")
                continue
        
        # Verificar partidos
        partidos = conn.execute(text("""
            SELECT COUNT(*) FROM partidos p
            JOIN torneos_parejas tp1 ON tp1.id = p.pareja1_id
            JOIN torneos_parejas tp2 ON tp2.id = p.pareja2_id
            WHERE tp1.jugador1_id = :tid OR tp1.jugador2_id = :tid
               OR tp2.jugador1_id = :tid OR tp2.jugador2_id = :tid
        """), {"tid": temp_id}).fetchone()[0]
        
        if partidos > 0:
            print(f"  ⚠️ Usuario {temp_id} tiene {partidos} partidos - NO SE ELIMINA")
            continue
        
        # Eliminar usuario
        print(f"  → Eliminando usuario {temp_id}...")
        # Primero eliminar historial_rating
        conn.execute(text("DELETE FROM historial_rating WHERE id_usuario = :tid"), {"tid": temp_id})
        conn.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = :tid"), {"tid": temp_id})
        conn.execute(text("DELETE FROM usuarios WHERE id_usuario = :tid"), {"tid": temp_id})
        print(f"  ✅ Usuario {temp_id} eliminado")
    
    conn.commit()
    print("\n✅ Limpieza completada!")
