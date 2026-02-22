"""Corregir rating y categoría de TODOS los temp según la categoría en que juegan.
categorias (tabla global, FK de usuarios.id_categoria):
  1=8va(M), 2=7ma(M), 3=6ta(M), 4=5ta(M), 5=4ta(M), 6=Libre(M), 7=Principiante(M)
  9=Principiante(F), 10=8va(F), 11=7ma(F), 12=6ta(F), 13=5ta(F), 14=Libre(F)

torneo_categorias (por torneo):
  87=4ta, 88=6ta, 89=8va, 91=6ta femenino (torneo 38)

Ratings:
  Principiante=249, 8va=749, 7ma=1099, 6ta=1299, 5ta=1499, 4ta=1699
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Mapeo: nombre torneo_categorias -> (id_categoria global, rating)
def get_cat_global(cat_nombre, sexo='masculino'):
    cat_nombre_lower = cat_nombre.lower().strip()
    if 'principiante' in cat_nombre_lower:
        return (9 if sexo == 'femenino' else 7, 249)
    elif '8va' in cat_nombre_lower:
        return (10 if sexo == 'femenino' else 1, 749)
    elif '7ma' in cat_nombre_lower:
        return (11 if sexo == 'femenino' else 2, 1099)
    elif '6ta' in cat_nombre_lower:
        if 'femenino' in cat_nombre_lower or sexo == 'femenino':
            return (12, 1299)
        return (3, 1299)
    elif '5ta' in cat_nombre_lower:
        return (13 if sexo == 'femenino' else 4, 1499)
    elif '4ta' in cat_nombre_lower:
        return (5, 1699)
    return None

with engine.connect() as c:
    # Obtener todos los temp en torneos con su categoría
    temps = c.execute(text("""
        SELECT DISTINCT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria,
               tp.categoria_id, tcat.nombre as cat_torneo, tcat.genero
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN torneos_parejas tp ON (tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario)
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        WHERE u.email LIKE '%@driveplus.temp'
        ORDER BY tcat.nombre, p.apellido, p.nombre
    """)).fetchall()
    
    print(f"Total temp en torneos: {len(temps)}")
    fixed = 0
    
    for t in temps:
        uid, nombre, apellido, rating_actual, cat_actual, cat_torneo_id, cat_torneo_nombre, genero = t
        
        sexo = 'femenino' if genero and 'femenino' in str(genero).lower() else 'masculino'
        result = get_cat_global(cat_torneo_nombre, sexo)
        
        if result is None:
            print(f"  ❓ {nombre} {apellido} (ID {uid}): cat '{cat_torneo_nombre}' no mapeada")
            continue
        
        cat_global_id, rating_correcto = result
        changes = []
        
        if rating_actual != rating_correcto:
            changes.append(f"rating {rating_actual}->{rating_correcto}")
        if cat_actual != cat_global_id:
            changes.append(f"cat {cat_actual}->{cat_global_id}")
        
        if changes:
            c.execute(text("""
                UPDATE usuarios SET rating = :rating, id_categoria = :cat
                WHERE id_usuario = :uid
            """), {"rating": rating_correcto, "cat": cat_global_id, "uid": uid})
            print(f"  ✏️ {nombre} {apellido} (ID {uid}) [{cat_torneo_nombre}]: {', '.join(changes)}")
            fixed += 1
    
    c.commit()
    print(f"\nTotal corregidos: {fixed}/{len(temps)}")
    
    # Verificación
    print(f"\n{'=' * 60}")
    print("VERIFICACIÓN")
    print("=" * 60)
    check = c.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria,
               tcat.nombre as cat_torneo, cat.nombre as cat_global
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN torneos_parejas tp ON (tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario)
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        JOIN categorias cat ON u.id_categoria = cat.id_categoria
        WHERE u.email LIKE '%@driveplus.temp'
        ORDER BY tcat.nombre, p.apellido
    """)).fetchall()
    
    por_cat = {}
    for r in check:
        por_cat.setdefault(r[5], []).append(r)
    for cat, users in sorted(por_cat.items()):
        print(f"\n  {cat}:")
        for u in users:
            print(f"    {u[1]} {u[2]} (ID {u[0]}): rating={u[3]}, cat_global={u[6]}")
