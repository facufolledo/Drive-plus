"""Migrar Emanuel Reyes (temp 516 -> real 553) y Aiken Moreno (temp 519 -> real 554) en T38.
Luego buscar zona E de 4ta con NN Romero y reemplazar por Tello Sergio / Chumbita Agustin."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # ============================================
    # PARTE 1: Migrar Emanuel Reyes y Aiken Moreno
    # ============================================
    migrations = [
        {"nombre": "Emanuel Reyes", "temp_id": 516, "real_id": 553},
        {"nombre": "Aiken Moreno", "temp_id": 519, "real_id": 554},
    ]
    
    for m in migrations:
        temp_id = m["temp_id"]
        real_id = m["real_id"]
        print(f"\n{'='*50}")
        print(f"MIGRANDO {m['nombre']}: temp {temp_id} -> real {real_id}")
        print(f"{'='*50}")
        
        # Rating y partidos del temp
        temp = c.execute(text("SELECT rating, partidos_jugados, id_categoria FROM usuarios WHERE id_usuario = :id"), {"id": temp_id}).fetchone()
        print(f"  Temp: rating={temp[0]} partidos={temp[1]} cat={temp[2]}")
        
        # Copiar rating/partidos/categoria del temp al real
        c.execute(text("""
            UPDATE usuarios SET rating = :r, partidos_jugados = :p, id_categoria = :cat
            WHERE id_usuario = :rid
        """), {"r": temp[0], "p": temp[1], "cat": temp[2], "rid": real_id})
        
        # Actualizar parejas: reemplazar temp por real
        updated_j1 = c.execute(text("UPDATE torneos_parejas SET jugador1_id = :rid WHERE jugador1_id = :tid AND torneo_id = 38"), 
                               {"rid": real_id, "tid": temp_id}).rowcount
        updated_j2 = c.execute(text("UPDATE torneos_parejas SET jugador2_id = :rid WHERE jugador2_id = :tid AND torneo_id = 38"),
                               {"rid": real_id, "tid": temp_id}).rowcount
        print(f"  Parejas actualizadas: j1={updated_j1} j2={updated_j2}")
        
        # Actualizar historial_rating
        hist_updated = c.execute(text("UPDATE historial_rating SET id_usuario = :rid WHERE id_usuario = :tid"),
                                {"rid": real_id, "tid": temp_id}).rowcount
        print(f"  Historial rating migrado: {hist_updated} registros")
        
        # Eliminar temp
        c.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = :tid"), {"tid": temp_id})
        c.execute(text("DELETE FROM usuarios WHERE id_usuario = :tid"), {"tid": temp_id})
        print(f"  Temp {temp_id} eliminado")
        
        # Verificar
        real = c.execute(text("""
            SELECT u.id_usuario, u.rating, u.partidos_jugados, pu.nombre, pu.apellido
            FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE u.id_usuario = :rid
        """), {"rid": real_id}).fetchone()
        print(f"  Real: ID {real[0]} {real[3]} {real[4]} rating={real[1]} partidos={real[2]}")
    
    # Verificar parejas
    print(f"\n{'='*50}")
    print("VERIFICACIÓN PAREJAS T38")
    print(f"{'='*50}")
    for pid in [639, 641]:
        p = c.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
                   p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
            FROM torneos_parejas tp
            JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
            JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
            WHERE tp.id = :pid
        """), {"pid": pid}).fetchone()
        print(f"  Pareja {p[0]}: {p[3]} / {p[4]} (j1={p[1]} j2={p[2]})")
    
    # ============================================
    # PARTE 2: Zona E de 4ta - buscar NN Romero
    # ============================================
    print(f"\n{'='*50}")
    print("ZONA E 4TA - BUSCAR NN ROMERO")
    print(f"{'='*50}")
    
    zonas_4ta = c.execute(text("""
        SELECT z.id, z.nombre, z.numero_orden FROM torneo_zonas z
        WHERE z.torneo_id = 38 AND z.categoria_id = 87
        ORDER BY z.numero_orden
    """)).fetchall()
    
    romero_pareja_id = None
    romero_zona_id = None
    for z in zonas_4ta:
        parejas = c.execute(text("""
            SELECT tp.id, tp.jugador1_id, tp.jugador2_id,
                   p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
            FROM torneo_zona_parejas tzp
            JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
            LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
            WHERE tzp.zona_id = :zid
        """), {"zid": z[0]}).fetchall()
        
        has_romero = False
        for p in parejas:
            if p[3] and 'Romero' in p[3] or p[4] and 'Romero' in p[4]:
                has_romero = True
                romero_pareja_id = p[0]
                romero_zona_id = z[0]
        
        if has_romero:
            print(f"  {z[1]} (ID {z[0]}):")
            for p in parejas:
                marker = " <-- ROMERO" if (p[3] and 'Romero' in p[3]) or (p[4] and 'Romero' in p[4]) else ""
                print(f"    Pareja {p[0]}: {p[3]} / {p[4]} j1={p[1]} j2={p[2]}{marker}")
    
    if romero_pareja_id:
        # Ver partidos de esta pareja
        partidos = c.execute(text("""
            SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.estado, p.elo_aplicado, p.ganador_pareja_id
            FROM partidos p
            WHERE p.id_torneo = 38 AND (p.pareja1_id = :pid OR p.pareja2_id = :pid)
        """), {"pid": romero_pareja_id}).fetchall()
        print(f"\n  Partidos de pareja {romero_pareja_id}:")
        for p in partidos:
            print(f"    P{p[0]}: p1={p[1]} vs p2={p[2]} estado={p[3]} elo={p[4]} ganador={p[5]}")
        
        # Ver jugadores de la pareja Romero
        romero_par = c.execute(text("SELECT jugador1_id, jugador2_id FROM torneos_parejas WHERE id = :pid"), {"pid": romero_pareja_id}).fetchone()
        print(f"\n  Jugadores pareja Romero: j1={romero_par[0]} j2={romero_par[1]}")
        for jid in [romero_par[0], romero_par[1]]:
            j = c.execute(text("""
                SELECT u.id_usuario, pu.nombre, pu.apellido, u.rating, u.password_hash
                FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
                WHERE u.id_usuario = :jid
            """), {"jid": jid}).fetchone()
            print(f"    ID {j[0]}: {j[1]} {j[2]} rating={j[3]} {'[TEMP]' if j[4]=='temp_no_login' else '[REAL]'}")
    
    # Buscar Tello y Chumbita
    print(f"\n  Buscando Tello y Chumbita en BD:")
    for search in ['tello', 'chumbita']:
        found = c.execute(text("""
            SELECT u.id_usuario, pu.nombre, pu.apellido, u.rating, u.password_hash, u.nombre_usuario
            FROM usuarios u JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE pu.nombre ILIKE :s OR pu.apellido ILIKE :s OR u.nombre_usuario ILIKE :s
        """), {"s": f"%{search}%"}).fetchall()
        for f in found:
            print(f"    ID {f[0]}: {f[1]} {f[2]} user={f[5]} rating={f[3]} {'[TEMP]' if f[4]=='temp_no_login' else '[REAL]'}")
    
    c.commit()
    print("\n✅ Migración de Reyes y Moreno completada")
    print("⏳ Zona E 4ta: info recopilada, falta crear temps Tello/Chumbita y reemplazar")
