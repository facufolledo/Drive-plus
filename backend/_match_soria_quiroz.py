import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Buscar temp con apellido Soria o Quiroz
    rows = c.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido, u.rating,
               tp.torneo_id, tcat.nombre as cat
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        LEFT JOIN torneos_parejas tp ON (tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario)
        LEFT JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        WHERE u.email LIKE '%@driveplus.temp'
        AND (LOWER(p.apellido) LIKE '%soria%' OR LOWER(p.apellido) LIKE '%quiroz%'
             OR LOWER(p.nombre) LIKE '%soria%' OR LOWER(p.nombre) LIKE '%quiroz%'
             OR LOWER(p.nombre) LIKE '%nicolas%' OR LOWER(p.nombre) LIKE '%farid%')
    """)).fetchall()
    for r in rows:
        print(f"  ID {r[0]}: {r[3]} {r[4]} ({r[1]}), rating={r[5]}, torneo={r[6]}, cat={r[7]}")
    if not rows:
        print("  No hay temp con esos nombres/apellidos")
