"""Verificar jugadores y solapamientos para nueva zona 6ta"""
import os, sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TORNEO_ID = 38
DURACION = timedelta(minutes=90)
CANCHAS = {76: "Cancha 5", 77: "Cancha 6", 78: "Cancha 7"}

# Parejas:
# Calderón Juan + Calderón Marcos
# Martinez Diego + Ceballos Ezequiel
# Quiroz Farid + Soria Nicolas

with engine.connect() as c:
    # 1. Buscar jugadores
    print("=" * 70)
    print("1. BUSCAR JUGADORES EN LA APP")
    print("=" * 70)
    nombres = [
        ("Diego", "Martinez"), ("Ezequiel", "Ceballos"),
        ("Juan", "Calderón"), ("Marcos", "Calderón"),
        ("Farid", "Quiroz"), ("Nicolas", "Soria"),
    ]
    for nom, ape in nombres:
        rows = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido
            FROM usuarios u JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.nombre) LIKE LOWER(:n) AND LOWER(p.apellido) LIKE LOWER(:a)
        """), {"n": f"%{nom}%", "a": f"%{ape}%"}).fetchall()
        if rows:
            for r in rows:
                is_temp = "@driveplus.temp" in (r[2] or "")
                print(f"  {'TEMP' if is_temp else 'REAL'}: {r[3]} {r[4]} -> ID={r[0]} user={r[1]}")
        else:
            print(f"  ❌ NO ENCONTRADO: {nom} {ape}")

    # 2. Juan Calderón - buscar en qué categoría está
    print(f"\n{'=' * 70}")
    print("2. JUAN CALDERÓN - PAREJAS EN TORNEO 38")
    print("=" * 70)
    # Buscar por apellido Calderón
    calderones = c.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.nombre_usuario
        FROM usuarios u JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.apellido) LIKE '%calder%'
    """)).fetchall()
    for cal in calderones:
        print(f"  {cal[1]} {cal[2]} (ID: {cal[0]}, user: {cal[3]})")
        # Buscar parejas en torneo 38
        parejas = c.execute(text("""
            SELECT tp.id, tp.categoria_id, tc.nombre,
                   p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
            FROM torneos_parejas tp
            JOIN torneo_categorias tc ON tp.categoria_id = tc.id
            JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
            JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
            WHERE tp.torneo_id = :t AND (tp.jugador1_id = :j OR tp.jugador2_id = :j)
        """), {"t": TORNEO_ID, "j": cal[0]}).fetchall()
        for p in parejas:
            print(f"    Pareja {p[0]} en {p[2]} (cat {p[1]}): {p[3]} / {p[4]}")

    # 3. Partidos de Juan Calderón el viernes
    print(f"\n{'=' * 70}")
    print("3. PARTIDOS DE CALDERÓN(ES) EL VIERNES 20/02")
    print("=" * 70)
    for cal in calderones:
        partidos = c.execute(text("""
            SELECT p.id_partido, p.fecha_hora, p.cancha_id, p.categoria_id,
                   p1n.nombre || ' ' || p1n.apellido || '/' || p2n.nombre || ' ' || p2n.apellido as p1_name,
                   p3n.nombre || ' ' || p3n.apellido || '/' || p4n.nombre || ' ' || p4n.apellido as p2_name
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
            JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
            JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
            JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
            WHERE p.id_torneo = :t AND p.fecha_hora IS NOT NULL
            AND (tp1.jugador1_id = :j OR tp1.jugador2_id = :j OR tp2.jugador1_id = :j OR tp2.jugador2_id = :j)
            ORDER BY p.fecha_hora
        """), {"t": TORNEO_ID, "j": cal[0]}).fetchall()
        if partidos:
            print(f"  {cal[1]} {cal[2]} (ID: {cal[0]}):")
            for p in partidos:
                f = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
                print(f"    P{p[0]} cat={p[3]} {f.strftime('%a %d/%m %H:%M')} cancha={p[2]} | {p[4]} vs {p[5]}")

    # 4. Canchas disponibles vie 15:00, 18:00, 21:00
    print(f"\n{'=' * 70}")
    print("4. CANCHAS DISPONIBLES VIE 20/02 a 15:00, 18:00, 21:00")
    print("=" * 70)
    all_partidos = c.execute(text("""
        SELECT id_partido, fecha_hora, cancha_id FROM partidos
        WHERE id_torneo = :t AND fecha_hora IS NOT NULL
    """), {"t": TORNEO_ID}).fetchall()

    for hora_str, hora in [("15:00", datetime(2026,2,20,15,0)), ("18:00", datetime(2026,2,20,18,0)), ("21:00", datetime(2026,2,20,21,0))]:
        fin = hora + DURACION
        print(f"\n  {hora_str}:")
        for cid, cname in CANCHAS.items():
            libre = True
            conflicto = None
            for p in all_partidos:
                if p[2] != cid:
                    continue
                pf = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
                pfin = pf + DURACION
                if hora < pfin and pf < fin:
                    libre = False
                    conflicto = f"P{p[0]} {pf.strftime('%H:%M')}"
                    break
            if libre:
                print(f"    ✅ {cname} LIBRE")
            else:
                print(f"    ❌ {cname} ocupada ({conflicto})")
