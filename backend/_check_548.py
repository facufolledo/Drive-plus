import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    for uid in [547, 548, 549, 550]:
        u = c.execute(text("SELECT id_usuario, nombre_usuario, email, rating FROM usuarios WHERE id_usuario = :id"), {"id": uid}).fetchone()
        if u:
            print(f"  ID {uid}: user={u[1]}, email={u[2]}, rating={u[3]}")
        else:
            print(f"  ID {uid}: NO EXISTE")
    # Buscar por nombre
    print("\nBuscar Ceballos:")
    rows = c.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email, p.nombre, p.apellido, u.rating
        FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.nombre_usuario ILIKE '%ceballos%' OR u.email ILIKE '%ceballos%'
        OR (p.apellido ILIKE '%ceballos%')
    """)).fetchall()
    for r in rows:
        print(f"  ID {r[0]}: user={r[1]}, email={r[2]}, {r[3]} {r[4]}, rating={r[5]}")
