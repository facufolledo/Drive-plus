"""Crear nueva zona en 6ta (cat 88) del T38 con 2 parejas + partido a las 16:00 sáb 21/02.
Pareja 1: Aguilar Marcelo / Bustos Patricio
Pareja 2: Aredes Martin / Rivarola Matias
6ta = cat 88, rating base 1299, cat_global 3
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # 1. Buscar si alguno ya existe
    print("=== BUSCAR JUGADORES ===")
    for nombre, apellido in [("Marcelo", "Aguilar"), ("Patricio", "Bustos"), ("Martin", "Aredes"), ("Matias", "Rivarola")]:
        found = c.execute(text("""
            SELECT u.id_usuario, pu.nombre, pu.apellido, u.rating, u.password_hash, u.nombre_usuario
            FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE pu.nombre ILIKE :n AND pu.apellido ILIKE :a
        """), {"n": f"%{nombre}%", "a": f"%{apellido}%"}).fetchall()
        if found:
            for f in found:
                print(f"  {f[1]} {f[2]}: ID {f[0]} user={f[5]} rating={f[3]} {'[TEMP]' if f[4]=='temp_no_login' else '[REAL]'}")
        else:
            print(f"  {nombre} {apellido}: NO encontrado, crear temp")
    
    # 2. Crear temps para los 4
    print("\n=== CREAR TEMPS ===")
    jugadores = []
    temps_data = [
        ("Marcelo", "Aguilar", "marcelo.aguilar.6ta"),
        ("Patricio", "Bustos", "patricio.bustos.6ta"),
        ("Martin", "Aredes", "martin.aredes.6ta"),
        ("Matias", "Rivarola", "matias.rivarola.6ta"),
    ]
    for nombre, apellido, username in temps_data:
        # Check if already exists
        existing = c.execute(text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"), {"u": username}).fetchone()
        if existing:
            jugadores.append(existing[0])
            print(f"  {nombre} {apellido}: ya existe ID {existing[0]}")
            continue
        
        # Check if real user exists
        real = c.execute(text("""
            SELECT u.id_usuario FROM usuarios u 
            JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE pu.nombre ILIKE :n AND pu.apellido ILIKE :a
            AND (u.password_hash IS NULL OR u.password_hash = '')
        """), {"n": f"%{nombre}%", "a": f"%{apellido}%"}).fetchone()
        if real:
            jugadores.append(real[0])
            print(f"  {nombre} {apellido}: usuario real ID {real[0]}")
            continue
        
        r = c.execute(text("""
            INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, id_categoria, partidos_jugados)
            VALUES (:user, :email, 'temp_no_login', 1299, 3, 0)
            RETURNING id_usuario
        """), {"user": username, "email": f"{username}@driveplus.temp"})
        uid = r.fetchone()[0]
        c.execute(text("INSERT INTO perfil_usuarios (id_usuario, nombre, apellido) VALUES (:uid, :n, :a)"),
                 {"uid": uid, "n": nombre, "a": apellido})
        jugadores.append(uid)
        print(f"  {nombre} {apellido}: creado temp ID {uid}")
    
    # 3. Contar zonas actuales en 6ta
    zonas_6ta = c.execute(text("""
        SELECT COUNT(*) FROM torneo_zonas WHERE torneo_id = 38 AND categoria_id = 88
    """)).fetchone()[0]
    zona_letra = chr(ord('A') + zonas_6ta)  # siguiente letra
    zona_orden = zonas_6ta + 1
    print(f"\n=== CREAR ZONA {zona_letra} (orden {zona_orden}) ===")
    
    # 4. Crear parejas
    parejas_data = [
        (jugadores[0], jugadores[1], "Aguilar / Bustos"),
        (jugadores[2], jugadores[3], "Aredes / Rivarola"),
    ]
    pareja_ids = []
    for j1, j2, nombre in parejas_data:
        r = c.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado)
            VALUES (38, 88, :j1, :j2, 'confirmada')
            RETURNING id
        """), {"j1": j1, "j2": j2})
        pid = r.fetchone()[0]
        pareja_ids.append(pid)
        print(f"  Pareja {pid}: {nombre} (j1={j1} j2={j2})")
    
    # 5. Crear zona
    r = c.execute(text("""
        INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
        VALUES (38, 88, :nombre, :orden)
        RETURNING id
    """), {"nombre": f"Zona {zona_letra}", "orden": zona_orden})
    zona_id = r.fetchone()[0]
    print(f"  Zona {zona_letra} creada: ID {zona_id}")
    
    for pid in pareja_ids:
        c.execute(text("INSERT INTO torneo_zona_parejas (zona_id, pareja_id) VALUES (:z, :p)"),
                 {"z": zona_id, "p": pid})
    
    # 6. Crear partido a las 16:00 sáb 21/02 - buscar cancha libre
    ocupadas = c.execute(text("""
        SELECT cancha_id FROM partidos
        WHERE id_torneo = 38 AND fecha_hora = '2026-02-21 16:00:00'
    """)).fetchall()
    ocupadas_ids = {r[0] for r in ocupadas}
    print(f"\n  Canchas ocupadas a las 16:00: {ocupadas_ids}")
    
    cancha_id = None
    for cid in [76, 77, 78, 79]:
        if cid not in ocupadas_ids:
            cancha_id = cid
            break
    
    cancha_nombre = c.execute(text("SELECT nombre FROM torneo_canchas WHERE id = :id"), {"id": cancha_id}).fetchone()[0]
    print(f"  Cancha asignada: {cancha_nombre} (ID {cancha_id})")
    
    r = c.execute(text("""
        INSERT INTO partidos (id_torneo, categoria_id, pareja1_id, pareja2_id, fecha, fecha_hora, cancha_id, fase, tipo, estado, id_creador)
        VALUES (38, 88, :p1, :p2, '2026-02-21', '2026-02-21 16:00:00', :cancha, 'zona', 'torneo', 'pendiente', 2)
        RETURNING id_partido
    """), {"p1": pareja_ids[0], "p2": pareja_ids[1], "cancha": cancha_id})
    partido_id = r.fetchone()[0]
    
    c.commit()
    
    print(f"\n=== RESUMEN ===")
    print(f"Zona {zona_letra} (ID {zona_id}) en 6ta T38")
    print(f"Pareja {pareja_ids[0]}: Aguilar/Bustos")
    print(f"Pareja {pareja_ids[1]}: Aredes/Rivarola")
    print(f"Partido P{partido_id}: sáb 21/02 16:00 | {cancha_nombre}")
