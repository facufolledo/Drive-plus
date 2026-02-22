"""Corregir temp del T38 que NO tienen historial: rating y categoría según su cat del torneo.
También corregir los que SÍ tienen historial pero empezaron con rating incorrecto (1299 en vez de 749 para 8va)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def torneo_cat_to_global(nombre, genero='masculino'):
    n = nombre.lower().strip()
    if 'principiante' in n: return (7, 249)
    if '8va' in n: return (1, 749)
    if '7ma' in n: return (2, 1099)
    if '6ta' in n:
        if 'femenino' in n or genero == 'femenino': return (12, 1299)
        return (3, 1299)
    if '5ta' in n: return (4, 1499)
    if '4ta' in n: return (5, 1699)
    return None

with engine.connect() as c:
    # Temp del T38
    temps = c.execute(text("""
        SELECT DISTINCT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria,
               tp.categoria_id, tcat.nombre as cat_torneo, tcat.genero
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN torneos_parejas tp ON (tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario)
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        WHERE u.email LIKE '%@driveplus.temp'
        AND tp.torneo_id = 38
        ORDER BY tcat.nombre, p.apellido
    """)).fetchall()
    
    print(f"Temp en T38: {len(temps)}")
    fixed = 0
    
    for t in temps:
        uid, nombre, apellido, rating, cat, cat_torneo_id, cat_torneo_nombre, genero = t
        cat_info = torneo_cat_to_global(cat_torneo_nombre, genero or 'masculino')
        if not cat_info:
            continue
        cat_global, rating_base = cat_info
        
        # Ver si tiene historial
        historial = c.execute(text("""
            SELECT id_historial, id_partido, rating_antes, delta, rating_despues
            FROM historial_rating WHERE id_usuario = :uid ORDER BY creado_en
        """), {"uid": uid}).fetchall()
        
        if historial:
            # Tiene historial - verificar si el rating_antes del primer partido era incorrecto
            primer = historial[0]
            if primer[2] != rating_base:
                # El rating_antes era incorrecto, recalcular toda la cadena
                print(f"\n  🔧 {nombre} {apellido} (ID {uid}) [{cat_torneo_nombre}]: historial con rating_antes incorrecto ({primer[2]} debería ser {rating_base})")
                rating_actual = rating_base
                for h in historial:
                    delta = h[3]
                    nuevo_antes = rating_actual
                    nuevo_despues = rating_actual + delta
                    c.execute(text("""
                        UPDATE historial_rating 
                        SET rating_antes = :antes, rating_despues = :despues
                        WHERE id_historial = :hid
                    """), {"antes": nuevo_antes, "despues": nuevo_despues, "hid": h[0]})
                    print(f"    P{h[1]}: {h[2]}+({h[3]})={h[4]} -> {nuevo_antes}+({delta})={nuevo_despues}")
                    rating_actual = nuevo_despues
                
                # Actualizar rating del usuario
                c.execute(text("UPDATE usuarios SET rating = :r, id_categoria = :c WHERE id_usuario = :uid"),
                         {"r": rating_actual, "c": cat_global, "uid": uid})
                print(f"    Rating final: {rating_actual}, cat: {cat_global}")
                fixed += 1
            elif cat != cat_global:
                c.execute(text("UPDATE usuarios SET id_categoria = :c WHERE id_usuario = :uid"),
                         {"c": cat_global, "uid": uid})
                print(f"  ✏️ {nombre} {apellido} (ID {uid}): cat {cat}->{cat_global}")
                fixed += 1
        else:
            # Sin historial - poner rating base
            changes = []
            if rating != rating_base:
                changes.append(f"rating {rating}->{rating_base}")
            if cat != cat_global:
                changes.append(f"cat {cat}->{cat_global}")
            
            if changes:
                c.execute(text("UPDATE usuarios SET rating = :r, id_categoria = :c WHERE id_usuario = :uid"),
                         {"r": rating_base, "c": cat_global, "uid": uid})
                print(f"  ✏️ {nombre} {apellido} (ID {uid}) [{cat_torneo_nombre}]: {', '.join(changes)}")
                fixed += 1
    
    c.commit()
    print(f"\nTotal corregidos: {fixed}")
    
    # Verificación final
    print(f"\n{'=' * 60}")
    print("VERIFICACIÓN T38")
    print("=" * 60)
    check = c.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria,
               tcat.nombre as cat_torneo
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN torneos_parejas tp ON (tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario)
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        WHERE u.email LIKE '%@driveplus.temp' AND tp.torneo_id = 38
        ORDER BY tcat.nombre, p.apellido
    """)).fetchall()
    por_cat = {}
    for r in check:
        por_cat.setdefault(r[5], []).append(r)
    for cat, users in sorted(por_cat.items()):
        print(f"\n  {cat}:")
        for u in users:
            print(f"    {u[1]} {u[2]} (ID {u[0]}): rating={u[3]}, cat={u[4]}")
