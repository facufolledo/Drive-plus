"""Restaurar historial de temp que jugaron en torneos ANTERIORES al 38.
Estos tienen historial que fue recalculado incorrectamente.
Necesitamos restaurar su rating_antes original basado en la categoría donde empezaron.

Afectados: Gula Saracho (162), Marcos Calderón (216), Matias Giordano (136), 
Bautista Oliva (200), Juan Calderón (201)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def cat_rating_base(nombre):
    n = nombre.lower()
    if 'principiante' in n: return 249
    if '8va' in n: return 749
    if '7ma' in n: return 1099
    if '6ta' in n: return 1299
    if '5ta' in n: return 1499
    if '4ta' in n: return 1699
    return None

def cat_global_id(nombre):
    n = nombre.lower()
    if 'principiante' in n: return 7
    if '8va' in n: return 1
    if '7ma' in n: return 2
    if '6ta' in n: return 3
    if '5ta' in n: return 4
    if '4ta' in n: return 5
    return None

with engine.connect() as c:
    # Usuarios que están en T38 Y en otros torneos
    multi = c.execute(text("""
        SELECT DISTINCT u.id_usuario, p.nombre, p.apellido
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.email LIKE '%@driveplus.temp'
        AND u.id_usuario IN (
            SELECT jugador1_id FROM torneos_parejas WHERE torneo_id = 38
            UNION SELECT jugador2_id FROM torneos_parejas WHERE torneo_id = 38
        )
        AND u.id_usuario IN (
            SELECT jugador1_id FROM torneos_parejas WHERE torneo_id != 38
            UNION SELECT jugador2_id FROM torneos_parejas WHERE torneo_id != 38
        )
        ORDER BY p.apellido
    """)).fetchall()
    
    print(f"Temp en T38 que también están en otros torneos: {len(multi)}")
    
    for m in multi:
        uid, nombre, apellido = m
        
        # Ver todos sus torneos
        torneos = c.execute(text("""
            SELECT DISTINCT tp.torneo_id, tcat.nombre as cat
            FROM torneos_parejas tp
            JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
            WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
            ORDER BY tp.torneo_id
        """), {"uid": uid}).fetchall()
        
        # Primer torneo = categoría original
        primer_torneo = torneos[0]
        rating_inicio = cat_rating_base(primer_torneo[1])
        
        # Categoría del T38
        t38_cats = [t for t in torneos if t[0] == 38]
        
        print(f"\n  {nombre} {apellido} (ID {uid}):")
        print(f"    Torneos: {[(t[0], t[1]) for t in torneos]}")
        print(f"    Rating inicio (primer torneo {primer_torneo[0]}, {primer_torneo[1]}): {rating_inicio}")
        
        # Recalcular historial desde el rating base correcto
        historial = c.execute(text("""
            SELECT id_historial, id_partido, rating_antes, delta, rating_despues
            FROM historial_rating WHERE id_usuario = :uid ORDER BY creado_en
        """), {"uid": uid}).fetchall()
        
        if historial and rating_inicio:
            rating_actual = rating_inicio
            for h in historial:
                delta = h[3]
                nuevo_antes = rating_actual
                nuevo_despues = rating_actual + delta
                if h[2] != nuevo_antes or h[4] != nuevo_despues:
                    c.execute(text("""
                        UPDATE historial_rating 
                        SET rating_antes = :antes, rating_despues = :despues
                        WHERE id_historial = :hid
                    """), {"antes": nuevo_antes, "despues": nuevo_despues, "hid": h[0]})
                    print(f"    P{h[1]}: {h[2]}+({h[3]})={h[4]} -> {nuevo_antes}+({delta})={nuevo_despues}")
                rating_actual = nuevo_despues
            
            # Actualizar rating del usuario
            # La categoría debe ser la del PRIMER torneo (donde empezó)
            cat_id = cat_global_id(primer_torneo[1])
            c.execute(text("UPDATE usuarios SET rating = :r, id_categoria = :c WHERE id_usuario = :uid"),
                     {"r": rating_actual, "c": cat_id, "uid": uid})
            print(f"    Rating final: {rating_actual}, cat: {cat_id} ({primer_torneo[1]})")
    
    c.commit()
    print("\n✅ Restaurados")
