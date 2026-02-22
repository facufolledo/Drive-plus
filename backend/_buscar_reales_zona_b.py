import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as c:
    nombres = [
        ("Santiago", "Rodríguez"), ("Matías", "Castelli"),
        ("Maximiliano", "Pérez"), ("Facundo", "Rodríguez"),
    ]
    for nom, ape in nombres:
        print(f"\n=== {nom} {ape} ===")
        rows = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.partidos_jugados,
                   p.nombre, p.apellido
            FROM usuarios u
            JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE LOWER(p.apellido) LIKE LOWER(:a)
            AND (LOWER(p.nombre) LIKE LOWER(:n) OR LOWER(p.nombre) LIKE LOWER(:n2))
            ORDER BY u.id_usuario
        """), {"a": f"%{ape.replace('í','i').replace('é','e')}%", "n": f"%{nom}%", "n2": f"%{nom.replace('í','i').replace('á','a').replace('é','e')}%"}).fetchall()
        if not rows:
            # Intentar sin acentos
            rows = c.execute(text("""
                SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.partidos_jugados,
                       p.nombre, p.apellido
                FROM usuarios u
                JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
                WHERE LOWER(p.apellido) LIKE LOWER(:a)
                ORDER BY u.id_usuario
            """), {"a": f"%{ape[:4].lower()}%"}).fetchall()
        for r in rows:
            is_temp = "@driveplus.temp" in (r[2] or "")
            print(f"  {'TEMP' if is_temp else 'REAL'} ID={r[0]} user={r[1]} email={r[2]} rating={r[3]} partidos={r[4]} | {r[5]} {r[6]}")
