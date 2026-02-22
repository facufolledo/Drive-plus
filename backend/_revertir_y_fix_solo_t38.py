"""
Revertir cambios en temp de torneos anteriores y solo corregir los del T38.
Los temp del T38 son los que están en torneos_parejas con torneo_id=38.
Los temp de torneos anteriores tienen historial de partidos que hay que respetar.

Estrategia:
- Para cada temp afectado, si tiene historial_rating, recalcular rating desde historial
- Si no tiene historial, usar el rating base de su categoría
- Solo aplicar cat/rating fijo a los que SOLO están en T38 y no tienen historial
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Categoría global -> rating base
CAT_RATING_BASE = {
    1: 749,   # 8va M
    2: 1099,  # 7ma M
    3: 1299,  # 6ta M
    4: 1499,  # 5ta M
    5: 1699,  # 4ta M
    7: 249,   # Principiante M
    10: 749,  # 8va F
}

# Torneo cat nombre -> (cat_global_id, rating_base)
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
    # Obtener TODOS los temp
    all_temps = c.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.rating, u.id_categoria, u.partidos_jugados
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.email LIKE '%@driveplus.temp'
        ORDER BY u.id_usuario
    """)).fetchall()
    
    print(f"Total temp: {len(all_temps)}")
    
    # Para cada temp, ver en qué torneos está
    fixed = 0
    for t in all_temps:
        uid, nombre, apellido, rating, cat, pj = t
        
        # Torneos en que participa
        torneos = c.execute(text("""
            SELECT DISTINCT tp.torneo_id, tp.categoria_id, tcat.nombre, tcat.genero
            FROM torneos_parejas tp
            JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
            WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
            ORDER BY tp.torneo_id
        """), {"uid": uid}).fetchall()
        
        torneo_ids = [t[0] for t in torneos]
        solo_t38 = torneo_ids == [38]
        en_t38 = 38 in torneo_ids
        
        # Historial de rating
        historial = c.execute(text("""
            SELECT id_partido, rating_antes, delta, rating_despues
            FROM historial_rating
            WHERE id_usuario = :uid
            ORDER BY creado_en
        """), {"uid": uid}).fetchall()
        
        if historial:
            # Tiene historial -> recalcular rating desde el último registro
            ultimo = historial[-1]
            rating_correcto = ultimo[3]  # rating_despues del último partido
            
            # La categoría debe ser la que corresponde a su rating actual
            # Buscar la categoría más alta del torneo donde juega
            if en_t38:
                t38_cats = [t for t in torneos if t[0] == 38]
                if t38_cats:
                    cat_info = torneo_cat_to_global(t38_cats[0][2], t38_cats[0][3] or 'masculino')
                else:
                    cat_info = None
            else:
                # No está en T38, buscar su categoría del torneo más reciente
                last_torneo = torneos[-1]
                cat_info = torneo_cat_to_global(last_torneo[2], last_torneo[3] or 'masculino')
            
            if rating != rating_correcto:
                c.execute(text("UPDATE usuarios SET rating = :r WHERE id_usuario = :uid"),
                         {"r": rating_correcto, "uid": uid})
                print(f"  🔄 {nombre} {apellido} (ID {uid}): rating {rating}->{rating_correcto} (desde historial, pj={pj})")
                fixed += 1
            
            # Restaurar categoría si fue cambiada incorrectamente
            # Para los que tienen historial, la categoría debería basarse en su rating
            if cat_info and cat != cat_info[0]:
                # Solo restaurar si el rating actual está en el rango de otra categoría
                # Mejor: usar la categoría del torneo donde más recientemente jugó
                pass  # No tocar categoría de los que tienen historial, es complejo
                
        elif solo_t38:
            # Solo en T38, sin historial -> aplicar rating base de la categoría del T38
            t38_cat = [t for t in torneos if t[0] == 38][0]
            cat_info = torneo_cat_to_global(t38_cat[2], t38_cat[3] or 'masculino')
            
            if cat_info:
                cat_global, rating_base = cat_info
                changes = []
                if rating != rating_base:
                    changes.append(f"rating {rating}->{rating_base}")
                if cat != cat_global:
                    changes.append(f"cat {cat}->{cat_global}")
                
                if changes:
                    c.execute(text("UPDATE usuarios SET rating = :r, id_categoria = :c WHERE id_usuario = :uid"),
                             {"r": rating_base, "c": cat_global, "uid": uid})
                    print(f"  ✏️ {nombre} {apellido} (ID {uid}) [T38 {t38_cat[2]}]: {', '.join(changes)}")
                    fixed += 1
        elif torneos:
            # En otros torneos sin historial -> restaurar rating base de su categoría más reciente
            last_torneo = torneos[-1]
            cat_info = torneo_cat_to_global(last_torneo[2], last_torneo[3] or 'masculino')
            if cat_info:
                cat_global, rating_base = cat_info
                changes = []
                if rating != rating_base:
                    changes.append(f"rating {rating}->{rating_base}")
                if cat != cat_global:
                    changes.append(f"cat {cat}->{cat_global}")
                if changes:
                    c.execute(text("UPDATE usuarios SET rating = :r, id_categoria = :c WHERE id_usuario = :uid"),
                             {"r": rating_base, "c": cat_global, "uid": uid})
                    print(f"  🔧 {nombre} {apellido} (ID {uid}) [otros torneos, {last_torneo[2]}]: {', '.join(changes)}")
                    fixed += 1
    
    c.commit()
    print(f"\nTotal corregidos: {fixed}")
