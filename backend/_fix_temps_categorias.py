"""
1. Borrar usuarios temp que fueron migrados a reales (538, 539, 524, 525, 532)
2. Corregir rating y categoría de TODOS los temp según la categoría en que juegan
   - 6ta principiante: 249
   - 8va: 749
   - 7ma: 1099
   - 6ta: 1299
   - 5ta: 1499
   - 4ta: 1699
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Mapeo categoría nombre -> rating inicial
CAT_RATING = {
    '6ta principiante': 249,
    'principiante': 249,
    '8va': 749,
    '7ma': 1099,
    '6ta': 1299,
    '6ta femenino': 1299,
    '5ta': 1499,
    '4ta': 1699,
}

with engine.connect() as c:
    # ============================================================
    # 1. Ver categorías disponibles en usuarios
    # ============================================================
    cats = c.execute(text("""
        SELECT DISTINCT id_categoria, 
               (SELECT nombre FROM torneo_categorias WHERE id = id_categoria LIMIT 1) as cat_name
        FROM usuarios WHERE id_categoria IS NOT NULL
        ORDER BY id_categoria
    """)).fetchall()
    print("Categorías en usuarios:")
    for cat in cats:
        print(f"  id_categoria={cat[0]}, nombre={cat[1]}")

    # Ver todas las categorías de torneo_categorias
    all_cats = c.execute(text("SELECT DISTINCT id, nombre FROM torneo_categorias ORDER BY id")).fetchall()
    print("\nTodas las torneo_categorias:")
    for cat in all_cats:
        print(f"  id={cat[0]}, nombre={cat[1]}")

    # ============================================================
    # 2. BORRAR TEMP MIGRADOS
    # ============================================================
    print(f"\n{'=' * 60}")
    print("BORRAR TEMP MIGRADOS")
    print("=" * 60)
    
    migrados = [538, 539, 524, 525, 532]  # Santiago, Castelli, Ferreyra, Gudiño, Álvaro Ferreyra
    for tid in migrados:
        info = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, p.nombre, p.apellido
            FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.id_usuario = :id
        """), {"id": tid}).fetchone()
        if not info:
            print(f"  ID {tid}: ya no existe")
            continue
        
        # Verificar que no esté en ninguna pareja activa
        en_parejas = c.execute(text("""
            SELECT COUNT(*) FROM torneos_parejas 
            WHERE jugador1_id = :tid OR jugador2_id = :tid
        """), {"tid": tid}).fetchone()[0]
        
        if en_parejas > 0:
            print(f"  ⚠️ ID {tid} ({info[2]} {info[3]}): todavía en {en_parejas} parejas, NO se borra")
            continue
        
        # Borrar perfil, luego usuario
        c.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = :id"), {"id": tid})
        c.execute(text("DELETE FROM usuarios WHERE id_usuario = :id"), {"id": tid})
        print(f"  🗑️ ID {tid} ({info[2]} {info[3]}): eliminado")

    # ============================================================
    # 3. CORREGIR RATING Y CATEGORÍA DE TODOS LOS TEMP
    # ============================================================
    print(f"\n{'=' * 60}")
    print("CORREGIR RATING Y CATEGORÍA DE TODOS LOS TEMP")
    print("=" * 60)
    
    # Obtener todos los temp que están en algún torneo
    temps = c.execute(text("""
        SELECT DISTINCT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria,
               tp.categoria_id, tcat.nombre as cat_torneo
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN torneos_parejas tp ON (tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario)
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        WHERE u.email LIKE '%@driveplus.temp'
        ORDER BY tcat.nombre, p.apellido, p.nombre
    """)).fetchall()
    
    fixed = 0
    for t in temps:
        uid, nombre, apellido, rating_actual, cat_actual, cat_torneo_id, cat_torneo_nombre = t
        
        # Determinar rating correcto según categoría del torneo
        rating_correcto = None
        for key, val in CAT_RATING.items():
            if key.lower() in cat_torneo_nombre.lower():
                rating_correcto = val
                break
        
        if rating_correcto is None:
            print(f"  ❓ {nombre} {apellido} (ID {uid}): cat '{cat_torneo_nombre}' no mapeada")
            continue
        
        needs_fix = False
        changes = []
        
        # Verificar rating
        if rating_actual != rating_correcto:
            changes.append(f"rating {rating_actual}->{rating_correcto}")
            needs_fix = True
        
        # Verificar categoría
        if cat_actual != cat_torneo_id:
            changes.append(f"cat {cat_actual}->{cat_torneo_id}")
            needs_fix = True
        
        if needs_fix:
            c.execute(text("""
                UPDATE usuarios SET rating = :rating, id_categoria = :cat
                WHERE id_usuario = :uid
            """), {"rating": rating_correcto, "cat": cat_torneo_id, "uid": uid})
            print(f"  ✏️ {nombre} {apellido} (ID {uid}) [{cat_torneo_nombre}]: {', '.join(changes)}")
            fixed += 1
        else:
            pass  # ya está bien
    
    c.commit()
    print(f"\n  Total temp corregidos: {fixed}/{len(temps)}")
    
    # ============================================================
    # VERIFICACIÓN: temp con rating incorrecto
    # ============================================================
    print(f"\n{'=' * 60}")
    print("VERIFICACIÓN FINAL")
    print("=" * 60)
    
    check = c.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria,
               tcat.nombre as cat_torneo
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN torneos_parejas tp ON (tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario)
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        WHERE u.email LIKE '%@driveplus.temp'
        ORDER BY tcat.nombre, p.apellido
    """)).fetchall()
    
    por_cat = {}
    for r in check:
        cat = r[5]
        por_cat.setdefault(cat, []).append(r)
    
    for cat, users in sorted(por_cat.items()):
        print(f"\n  {cat}:")
        for u in users:
            print(f"    {u[1]} {u[2]} (ID {u[0]}): rating={u[3]}, id_categoria={u[4]}")
