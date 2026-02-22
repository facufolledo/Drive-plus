import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    for user in ['nsoria71', 'charlifarid']:
        u = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.id_categoria, u.partidos_jugados,
                   p.nombre, p.apellido
            FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.nombre_usuario = :user OR u.email = :email
        """), {"user": user, "email": f"{user}@gmail.com"}).fetchone()
        if u:
            print(f"  {u[1]} (ID {u[0]}): {u[6]} {u[7]}, email={u[2]}, rating={u[3]}, cat={u[4]}, pj={u[5]}")
        else:
            print(f"  {user}: NO ENCONTRADO")
