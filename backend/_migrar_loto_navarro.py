"""Migrar Juan Loto (515->603) y Martin Navarro (591->602)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

migraciones = [
    (515, 603, "Juan Loto"),
    (591, 602, "Martin Navarro"),
]

with engine.connect() as conn:
    print("=== MIGRANDO USUARIOS ===\n")
    
    for temp_id, real_id, nombre in migraciones:
        print(f"\n--- {nombre}: {temp_id} -> {real_id} ---")
        
        # Verificar parejas del temp
        parejas = conn.execute(text("""
            SELECT tp.id, tp.torneo_id, tp.categoria_id,
                   CASE WHEN tp.jugador1_id = :tid THEN 'j1' ELSE 'j2' END as posicion
            FROM torneos_parejas tp
            WHERE tp.jugador1_id = :tid OR tp.jugador2_id = :tid
        """), {"tid": temp_id}).fetchall()
        
        if parejas:
            print(f"  Migrando {len(parejas)} parejas...")
            for p in parejas:
                if p[3] == 'j1':
                    conn.execute(text("UPDATE torneos_parejas SET jugador1_id = :real WHERE id = :pid"),
                                {"real": real_id, "pid": p[0]})
                else:
                    conn.execute(text("UPDATE torneos_parejas SET jugador2_id = :real WHERE id = :pid"),
                                {"real": real_id, "pid": p[0]})
                print(f"    ✅ Pareja {p[0]} (T{p[1]} Cat{p[2]})")
        else:
            print(f"  Sin parejas")
        
        # Copiar rating y partidos del temp al real
        temp_data = conn.execute(text("""
            SELECT rating, partidos_jugados, id_categoria
            FROM usuarios WHERE id_usuario = :tid
        """), {"tid": temp_id}).fetchone()
        
        if temp_data and temp_data[1] > 0:  # Si tiene partidos jugados
            print(f"  Actualizando rating: {temp_data[0]}, partidos: {temp_data[1]}, cat: {temp_data[2]}")
            conn.execute(text("""
                UPDATE usuarios 
                SET rating = :rating, partidos_jugados = :pj, id_categoria = :cat
                WHERE id_usuario = :real
            """), {"rating": temp_data[0], "pj": temp_data[1], "cat": temp_data[2], "real": real_id})
        
        # Migrar historial_rating
        historial = conn.execute(text("""
            SELECT COUNT(*) FROM historial_rating WHERE id_usuario = :tid
        """), {"tid": temp_id}).fetchone()[0]
        
        if historial > 0:
            print(f"  Migrando {historial} registros de historial...")
            conn.execute(text("""
                UPDATE historial_rating SET id_usuario = :real WHERE id_usuario = :temp
            """), {"real": real_id, "temp": temp_id})
        
        # Eliminar temp
        print(f"  Eliminando temp {temp_id}...")
        conn.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = :tid"), {"tid": temp_id})
        conn.execute(text("DELETE FROM usuarios WHERE id_usuario = :tid"), {"tid": temp_id})
        print(f"  ✅ {nombre} migrado correctamente")
    
    conn.commit()
    print("\n✅ Todas las migraciones completadas!")
