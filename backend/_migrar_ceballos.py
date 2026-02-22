"""Migrar Ezequiel Ceballos: temp 547 -> real 548"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # Diagnóstico
    for uid, label in [(547, "TEMP"), (548, "REAL")]:
        u = c.execute(text("SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.id_categoria, u.partidos_jugados FROM usuarios u WHERE u.id_usuario = :id"), {"id": uid}).fetchone()
        p = c.execute(text("SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
        if p:
            print(f"  {label} (ID {uid}): {p[0]} {p[1]}, user={u[1]}, email={u[2]}, rating={u[3]}, cat={u[4]}, pj={u[5]}")
        else:
            print(f"  {label} (ID {uid}): SIN PERFIL, user={u[1]}, email={u[2]}, rating={u[3]}, cat={u[4]}, pj={u[5]}")
            # Copiar perfil del temp
            tp = c.execute(text("SELECT nombre, apellido FROM perfil_usuarios WHERE id_usuario = 547")).fetchone()
            if tp:
                c.execute(text("INSERT INTO perfil_usuarios (id_usuario, nombre, apellido) VALUES (:uid, :n, :a)"),
                         {"uid": uid, "n": tp[0], "a": tp[1]})
                print(f"    Perfil creado: {tp[0]} {tp[1]}")

    # Migrar parejas
    r1 = c.execute(text("UPDATE torneos_parejas SET jugador1_id = 548 WHERE jugador1_id = 547 AND torneo_id = 38"), {}).rowcount
    r2 = c.execute(text("UPDATE torneos_parejas SET jugador2_id = 548 WHERE jugador2_id = 547 AND torneo_id = 38"), {}).rowcount
    print(f"\n  torneos_parejas: {r1+r2} actualizadas")

    # Migrar historial_rating
    r3 = c.execute(text("UPDATE historial_rating SET id_usuario = 548 WHERE id_usuario = 547"), {}).rowcount
    print(f"  historial_rating: {r3} registros migrados")

    # Actualizar rating y pj del real con los del temp
    temp = c.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = 547")).fetchone()
    c.execute(text("UPDATE usuarios SET rating = :r, partidos_jugados = :pj, id_categoria = 3 WHERE id_usuario = 548"),
             {"r": temp[0], "pj": temp[1]})
    print(f"  Real (548): rating={temp[0]}, pj={temp[1]}, cat=3 (6ta)")

    # Borrar temp
    en_parejas = c.execute(text("SELECT COUNT(*) FROM torneos_parejas WHERE jugador1_id = 547 OR jugador2_id = 547")).fetchone()[0]
    if en_parejas == 0:
        c.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = 547"))
        c.execute(text("DELETE FROM usuarios WHERE id_usuario = 547"))
        print(f"  🗑️ Temp 547 eliminado")
    else:
        print(f"  ⚠️ Temp 547 aún en {en_parejas} parejas, no se borra")

    c.commit()
    print("\n✅ Migrado")
