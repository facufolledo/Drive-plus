"""Crear Zona E en 8va (cat 89) del T38 con 2 parejas + 1 partido.
Pareja 1: Agustin Martinez (temp ID 170) + Sofia Salomon (real, user sofivictoria_2)
Pareja 2: Tiago Córdoba (temp nuevo) + Camilo Nieto (temp nuevo, distinto al ID 504)

8va = cat 89, rating base 749, cat_global 1 (8va M)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # 1. Verificar jugadores existentes
    print("=" * 60)
    print("1. VERIFICAR JUGADORES")
    print("=" * 60)
    
    # Agustin Martinez temp ID 170
    am = c.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria
        FROM usuarios u JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.id_usuario = 170
    """)).fetchone()
    print(f"  Agustin Martinez: ID {am[0]}, {am[1]} {am[2]}, rating={am[3]}, cat={am[4]}")
    
    # Sofia Salomon (sofivictoria_2)
    ss = c.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, p.nombre, p.apellido, u.rating, u.id_categoria
        FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.nombre_usuario = 'sofivictoria_2'
    """)).fetchone()
    if ss:
        print(f"  Sofia Salomon: ID {ss[0]}, user={ss[1]}, {ss[2]} {ss[3]}, rating={ss[4]}, cat={ss[5]}")
    else:
        print("  ❌ sofivictoria_2 NO ENCONTRADO")
        sys.exit(1)
    
    # 2. Crear temp para Tiago Córdoba y Camilo Nieto
    print(f"\n{'=' * 60}")
    print("2. CREAR TEMP NUEVOS")
    print("=" * 60)
    
    temps_to_create = [
        ("Tiago", "Córdoba", "tiago.cordoba.8va", 749, 1),
        ("Camilo", "Nieto", "camilo.nieto.8va", 749, 1),
    ]
    
    new_ids = {}
    for nombre, apellido, username, rating, cat in temps_to_create:
        # Verificar si ya existe
        existing = c.execute(text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"), {"u": username}).fetchone()
        if existing:
            new_ids[f"{nombre} {apellido}"] = existing[0]
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
        
        new_ids[f"{nombre} {apellido}"] = uid
        print(f"  {nombre} {apellido}: creado ID {uid}")
    
    tiago_id = new_ids["Tiago Córdoba"]
    camilo_id = new_ids["Camilo Nieto"]
    agustin_id = 170  # temp existente
    sofia_id = ss[0]
    
    # Actualizar Agustin Martinez a 8va si no lo está
    c.execute(text("UPDATE usuarios SET rating = 749, id_categoria = 1 WHERE id_usuario = :uid AND rating != 749"),
             {"uid": agustin_id})
    
    # 3. Crear parejas en 8va (cat 89)
    print(f"\n{'=' * 60}")
    print("3. CREAR PAREJAS")
    print("=" * 60)
    
    parejas = [
        (agustin_id, sofia_id, "Martinez / Salomon"),
        (tiago_id, camilo_id, "Córdoba / Nieto"),
    ]
    
    pareja_ids = []
    for j1, j2, nombre in parejas:
        r = c.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, nombre_pareja, estado)
            VALUES (38, 89, :j1, :j2, :nombre, 'confirmada')
            RETURNING id
        """), {"j1": j1, "j2": j2, "nombre": nombre})
        pid = r.fetchone()[0]
        pareja_ids.append(pid)
        print(f"  Pareja {pid}: {nombre} (j1={j1}, j2={j2})")
    
    # 4. Crear Zona E
    print(f"\n{'=' * 60}")
    print("4. CREAR ZONA E")
    print("=" * 60)
    
    r = c.execute(text("""
        INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
        VALUES (38, 89, 'Zona E', 5)
        RETURNING id
    """))
    zona_id = r.fetchone()[0]
    print(f"  Zona E creada: ID {zona_id}")
    
    # Asignar parejas a la zona
    for pid in pareja_ids:
        c.execute(text("INSERT INTO torneo_zona_parejas (zona_id, pareja_id) VALUES (:z, :p)"),
                 {"z": zona_id, "p": pid})
    print(f"  Parejas asignadas a zona")
    
    # 5. Crear partido (zona de 2 = 1 partido)
    print(f"\n{'=' * 60}")
    print("5. CREAR PARTIDO")
    print("=" * 60)
    
    # Verificar canchas libres a las 23:00 del viernes 20/02
    ocupadas = c.execute(text("""
        SELECT cancha_id, tc.nombre FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        WHERE p.id_torneo = 38 AND p.fecha_hora = '2026-02-20 23:00:00'
    """)).fetchall()
    print(f"  Canchas ocupadas a las 23:00: {[(r[0], r[1]) for r in ocupadas]}")
    
    # Buscar cancha libre (76=C5, 77=C6, 78=C7)
    ocupadas_ids = {r[0] for r in ocupadas}
    cancha_id = None
    for cid in [76, 77, 78]:
        if cid not in ocupadas_ids:
            cancha_id = cid
            break
    if not cancha_id:
        cancha_id = 79  # C8
    
    cancha_nombre = c.execute(text("SELECT nombre FROM torneo_canchas WHERE id = :id"), {"id": cancha_id}).fetchone()[0]
    print(f"  Cancha asignada: {cancha_nombre} (ID {cancha_id})")
    
    r = c.execute(text("""
        INSERT INTO partidos (id_torneo, categoria_id, pareja1_id, pareja2_id, fecha, fecha_hora, cancha_id, fase, tipo, estado, id_creador)
        VALUES (38, 89, :p1, :p2, '2026-02-20', '2026-02-20 23:00:00', :cancha, 'zona', 'torneo', 'pendiente', 2)
        RETURNING id_partido
    """), {"p1": pareja_ids[0], "p2": pareja_ids[1], "cancha": cancha_id})
    partido_id = r.fetchone()[0]
    print(f"  Partido P{partido_id}: {parejas[0][2]} vs {parejas[1][2]} | Vie 23:00 | {cancha_nombre}")
    
    c.commit()
    
    # Resumen
    print(f"\n{'=' * 60}")
    print("RESUMEN")
    print("=" * 60)
    print(f"  Zona E (ID {zona_id}) en 8va")
    print(f"  Pareja {pareja_ids[0]}: Agustin Martinez (ID {agustin_id}) + Sofia Salomon (ID {sofia_id})")
    print(f"  Pareja {pareja_ids[1]}: Tiago Córdoba (ID {tiago_id}) + Camilo Nieto (ID {camilo_id})")
    print(f"  Partido P{partido_id}: sin horario asignado aún")
