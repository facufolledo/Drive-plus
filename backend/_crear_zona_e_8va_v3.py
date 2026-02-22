"""Crear Zona E en 8va (cat 89) del T38 - v3 (fix columnas).
Los temps 549 (Tiago) y 550 (Camilo) ya fueron creados en v2.
Solo falta: crear parejas, zona, partido + actualizar Agustin a 8va.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    agustin_id = 170
    sofia_id = 76  # sofivictoria_2

    # Crear temps Tiago y Camilo (v2 hizo rollback)
    temps = [
        ("Tiago", "Córdoba", "tiago.cordoba.8va", 749, 1),
        ("Camilo", "Nieto", "camilo.nieto.8va", 749, 1),
    ]
    new_ids = {}
    for nombre, apellido, username, rating, cat in temps:
        existing = c.execute(text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"), {"u": username}).fetchone()
        if existing:
            new_ids[nombre] = existing[0]
            print(f"  {nombre} {apellido}: ya existe ID {existing[0]}")
            continue
        r = c.execute(text("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, id_categoria, partidos_jugados)
            VALUES (:user, :email, 'temp_no_login', :rating, :cat, 0)
            RETURNING id_usuario
        """), {"user": username, "email": f"{username}@driveplus.temp", "rating": rating, "cat": cat})
        uid = r.fetchone()[0]
        c.execute(text("INSERT INTO perfil_usuarios (id_usuario, nombre, apellido) VALUES (:uid, :n, :a)"),
                 {"uid": uid, "n": nombre, "a": apellido})
        new_ids[nombre] = uid
        print(f"  {nombre} {apellido}: creado ID {uid}")

    tiago_id = new_ids["Tiago"]
    camilo_id = new_ids["Camilo"]

    # Verificar todos
    for uid, name in [(agustin_id, "Agustin Martinez"), (sofia_id, "Sofia Salomon"),
                      (tiago_id, "Tiago Córdoba"), (camilo_id, "Camilo Nieto")]:
        r = c.execute(text("SELECT id_usuario FROM usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
        print(f"  {'✅' if r else '❌'} {name} ID {uid}")
        if not r:
            sys.exit(1)

    # Actualizar Agustin Martinez a 8va (rating 749, cat 1)
    c.execute(text("UPDATE usuarios SET rating = 749, id_categoria = 1 WHERE id_usuario = :uid"), {"uid": agustin_id})
    print(f"\n  Agustin Martinez actualizado a rating=749, cat=1 (8va)")

    # Crear parejas (sin nombre_pareja)
    print(f"\n--- CREAR PAREJAS ---")
    parejas = [
        (agustin_id, sofia_id, "Martinez / Salomon"),
        (tiago_id, camilo_id, "Córdoba / Nieto"),
    ]
    pareja_ids = []
    for j1, j2, label in parejas:
        r = c.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado)
            VALUES (38, 89, :j1, :j2, 'confirmada')
            RETURNING id
        """), {"j1": j1, "j2": j2})
        pid = r.fetchone()[0]
        pareja_ids.append(pid)
        print(f"  Pareja {pid}: {label} (j1={j1}, j2={j2})")

    # Crear Zona E
    print(f"\n--- CREAR ZONA E ---")
    r = c.execute(text("""
        INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
        VALUES (38, 89, 'Zona E', 5)
        RETURNING id
    """))
    zona_id = r.fetchone()[0]
    print(f"  Zona E: ID {zona_id}")

    for pid in pareja_ids:
        c.execute(text("INSERT INTO torneo_zona_parejas (zona_id, pareja_id) VALUES (:z, :p)"),
                 {"z": zona_id, "p": pid})
    print(f"  Parejas asignadas a zona")

    # Crear partido - viernes 20/02 a las 23:00
    print(f"\n--- CREAR PARTIDO ---")
    ocupadas = c.execute(text("""
        SELECT cancha_id FROM partidos
        WHERE id_torneo = 38 AND fecha_hora = '2026-02-20 23:00:00'
    """)).fetchall()
    ocupadas_ids = {r[0] for r in ocupadas}
    print(f"  Canchas ocupadas a 23:00: {ocupadas_ids}")

    cancha_id = None
    for cid in [76, 77, 78, 79]:
        if cid not in ocupadas_ids:
            cancha_id = cid
            break
    if not cancha_id:
        print("  ❌ No hay cancha libre a las 23:00!")
        sys.exit(1)

    cancha_nombre = c.execute(text("SELECT nombre FROM torneo_canchas WHERE id = :id"), {"id": cancha_id}).fetchone()[0]

    r = c.execute(text("""
        INSERT INTO partidos (id_torneo, categoria_id, pareja1_id, pareja2_id, fecha, fecha_hora, cancha_id, fase, tipo, estado, id_creador)
        VALUES (38, 89, :p1, :p2, '2026-02-20', '2026-02-20 23:00:00', :cancha, 'zona', 'torneo', 'pendiente', 2)
        RETURNING id_partido
    """), {"p1": pareja_ids[0], "p2": pareja_ids[1], "cancha": cancha_id})
    partido_id = r.fetchone()[0]
    print(f"  Partido P{partido_id}: Pareja {pareja_ids[0]} vs {pareja_ids[1]} | Vie 20/02 23:00 | {cancha_nombre}")

    c.commit()

    print(f"\n=== RESUMEN ===")
    print(f"  Zona E (ID {zona_id}) en 8va (cat 89)")
    print(f"  Pareja {pareja_ids[0]}: Martinez/Salomon ({agustin_id}+{sofia_id})")
    print(f"  Pareja {pareja_ids[1]}: Córdoba/Nieto ({tiago_id}+{camilo_id})")
    print(f"  Partido P{partido_id}: Vie 20/02 23:00 en {cancha_nombre}")
