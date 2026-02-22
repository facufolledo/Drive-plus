import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))
with e.connect() as c:
    # Todos los temp del T38 con su estado actual
    rows = c.execute(text("""
        SELECT DISTINCT u.id_usuario, p.nombre, p.apellido, u.rating, 
               cat.nombre as cat_global, tcat.nombre as cat_torneo, u.partidos_jugados
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN torneos_parejas tp ON (tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario)
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        LEFT JOIN categorias cat ON u.id_categoria = cat.id_categoria
        WHERE u.email LIKE '%@driveplus.temp' AND tp.torneo_id = 38
        ORDER BY tcat.nombre, u.rating DESC
    """)).fetchall()
    
    por_cat = {}
    for r in rows:
        por_cat.setdefault(r[5], []).append(r)
    
    for cat, users in sorted(por_cat.items()):
        print(f"\n{cat}:")
        for u in users:
            flag = " ⚠️" if u[4] and u[4].lower() != cat.lower().split()[0] else ""
            print(f"  {u[1]} {u[2]} (ID {u[0]}): rating={u[3]}, cat_global={u[4]}, pj={u[6]}{flag}")
