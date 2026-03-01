"""Migrar duplicados CORRECTAMENTE: mantener rating/cat del real, sumar partidos"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
engine = create_engine(os.getenv("DATABASE_URL"))

# (temp_id, real_id, nombre)
migraciones = [
    (552, 504, "Camilo Nieto"),
    (124, 80, "Juan Pablo Romero"),
    (518, 232, "Emanuel/Nahuel Toledo"),
    (492, 26, "Maxi/Matias Vega"),
]

with engine.connect() as conn:
    print("=== MIGRANDO DUPLICADOS (CORRECTO) ===\n")
    
    for temp_id, real_id, nombre in migraciones:
        print(f"\n--- {nombre}: {temp_id} -> {real_id} ---")
        
        # Obtener datos actuales
        temp_data = conn.execute(text("""
            SELECT rating, partidos_jugados, id_categoria
            FROM usuarios WHERE id_usuario = :tid
        """), {"tid": temp_id}).fetchone()
        
        real_data = conn.execute(text("""
            SELECT rating, partidos_jugados, id_categoria
            FROM usuarios WHERE id_usuario = :rid
        """), {"rid": real_id}).fetchone()
        
        print(f"  Temp: Rating={temp_data[0]}, PJ={temp_data[1]}, Cat={temp_data[2]}")
        print(f"  Real: Rating={real_data[0]}, PJ={real_data[1]}, Cat={real_data[2]}")
        
        # Migrar parejas
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
        
        # SOLO sumar partidos jugados (mantener rating y cat del real)
        nuevos_pj = real_data[1] + temp_data[1]
        print(f"  Actualizando partidos: {real_data[1]} + {temp_data[1]} = {nuevos_pj}")
        conn.execute(text("""
            UPDATE usuarios 
            SET partidos_jugados = :pj
            WHERE id_usuario = :real
        """), {"pj": nuevos_pj, "real": real_id})
        
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
