"""Investigar el check constraint partidos_fase_check"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    # 1. Ver el constraint definition
    print("=== CHECK CONSTRAINT ===")
    rows = c.execute(text("""
        SELECT conname, pg_get_constraintdef(oid) 
        FROM pg_constraint 
        WHERE conname LIKE '%fase%'
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]}")

    # 2. Ver valores de fase usados en partidos existentes
    print("\n=== VALORES DE FASE EN PARTIDOS ===")
    rows = c.execute(text("SELECT DISTINCT fase FROM partidos")).fetchall()
    for r in rows:
        print(f"  '{r[0]}'")

    # 3. Ver un partido existente del torneo 38 como referencia
    print("\n=== EJEMPLO PARTIDO T38 ===")
    r = c.execute(text("""
        SELECT id_partido, fase, estado, origen, id_creador, fecha, fecha_hora, cancha_id
        FROM partidos WHERE id_torneo = 38 LIMIT 1
    """)).fetchone()
    if r:
        print(f"  P{r[0]}: fase='{r[1]}', estado='{r[2]}', origen='{r[3]}', creador={r[4]}, fecha={r[5]}, fecha_hora={r[6]}, cancha={r[7]}")

    # 4. Verificar que zona 207 existe con sus parejas
    print("\n=== ZONA 207 ===")
    z = c.execute(text("SELECT id, nombre, categoria_id FROM torneo_zonas WHERE id = 207")).fetchone()
    if z:
        print(f"  Zona: {z[1]} (cat {z[2]})")
        parejas = c.execute(text("""
            SELECT zp.pareja_id, p1.nombre || ' ' || p1.apellido, p2.nombre || ' ' || p2.apellido
            FROM torneo_zona_parejas zp
            JOIN torneos_parejas tp ON zp.pareja_id = tp.id
            JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
            JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
            WHERE zp.zona_id = 207
        """)).fetchall()
        for p in parejas:
            print(f"  Pareja {p[0]}: {p[1]} / {p[2]}")
    else:
        print("  ❌ Zona 207 NO existe")

    # 5. Verificar si ya hay partidos en zona 207
    print("\n=== PARTIDOS EN ZONA 207 ===")
    pts = c.execute(text("SELECT id_partido FROM partidos WHERE zona_id = 207")).fetchall()
    if pts:
        for p in pts:
            print(f"  P{p[0]}")
    else:
        print("  Ninguno aún")
