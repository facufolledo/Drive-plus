"""Reemplazar pareja 643 (NN Ocampo/NN Romero) por Tello Sergio (temp nuevo) / Chumbita Agustin (real 193).
Pareja 643 en Zona E de 4ta, partido P403 pendiente sin ELO."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # 1. Crear temp Tello Sergio (4ta = 1699, cat 5)
    r = c.execute(text("""
        INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, id_categoria, partidos_jugados)
        VALUES ('sergio.tello.4ta', 'sergio.tello.4ta@driveplus.temp', 'temp_no_login', 1699, 5, 0)
        RETURNING id_usuario
    """))
    tello_id = r.fetchone()[0]
    c.execute(text("INSERT INTO perfil_usuarios (id_usuario, nombre, apellido) VALUES (:uid, 'Sergio', 'Tello')"),
             {"uid": tello_id})
    print(f"Tello Sergio creado: ID {tello_id}")
    
    chumbita_id = 193
    
    # 2. Actualizar pareja 643: reemplazar jugadores
    c.execute(text("""
        UPDATE torneos_parejas SET jugador1_id = :j1, jugador2_id = :j2
        WHERE id = 643
    """), {"j1": tello_id, "j2": chumbita_id})
    print(f"Pareja 643 actualizada: j1={tello_id} (Tello) j2={chumbita_id} (Chumbita)")
    
    # 3. Eliminar temps viejos (521=NN Ocampo, 522=NN Romero)
    # Verificar que no estén en otras parejas
    for tid in [521, 522]:
        otras = c.execute(text("""
            SELECT id FROM torneos_parejas WHERE (jugador1_id = :tid OR jugador2_id = :tid) AND id != 643
        """), {"tid": tid}).fetchall()
        if otras:
            print(f"  ⚠️ Temp {tid} está en otras parejas: {[o[0] for o in otras]}, NO se elimina")
        else:
            c.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = :tid"), {"tid": tid})
            c.execute(text("DELETE FROM usuarios WHERE id_usuario = :tid"), {"tid": tid})
            print(f"  Temp {tid} eliminado")
    
    c.commit()
    
    # Verificar
    print(f"\n--- VERIFICACIÓN ---")
    p = c.execute(text("""
        SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
               p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
        FROM torneos_parejas tp
        JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
        JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
        WHERE tp.id = 643
    """)).fetchone()
    print(f"Pareja {p[0]}: {p[3]} / {p[4]} (j1={p[1]} j2={p[2]})")
    
    partido = c.execute(text("""
        SELECT p.id_partido, p.estado FROM partidos p
        WHERE p.id_torneo = 38 AND (p.pareja1_id = 643 OR p.pareja2_id = 643)
    """)).fetchall()
    for pt in partido:
        print(f"Partido P{pt[0]}: estado={pt[1]}")
