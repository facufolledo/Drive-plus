import os
from difflib import SequenceMatcher
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
e = create_engine(os.getenv("DATABASE_URL"))

users = [
    'calderariel10', 'gigeri5700', 'albaro.tomas.ferreyra', 'corzothomas14',
    'aguirremariabelen', 'jereaa05', 'juandiegocrdb', 'caijoaquinv0912',
    'francoalegree323', 'mateo.algarrilla'
]

def sim(a, b):
    if not a or not b: return 0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

with e.connect() as c:
    # Info de cada user
    print("=" * 70)
    print("USUARIOS REALES")
    print("=" * 70)
    reales = []
    for user in users:
        u = c.execute(text("""
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rating, u.id_categoria,
                   COALESCE(p.nombre,'') as nombre, COALESCE(p.apellido,'') as apellido
            FROM usuarios u LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            WHERE u.nombre_usuario = :user
        """), {"user": user}).fetchone()
        if u:
            print(f"  {u[1]} (ID {u[0]}): {u[5]} {u[6]}, rating={u[3]}, cat={u[4]}")
            reales.append(u)
        else:
            print(f"  {user}: NO ENCONTRADO")

    # Temp del T38
    temps = c.execute(text("""
        SELECT DISTINCT u.id_usuario, COALESCE(p.nombre,'') as nombre,
               COALESCE(p.apellido,'') as apellido, u.rating,
               tcat.nombre as cat_torneo
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN torneos_parejas tp ON (tp.jugador1_id = u.id_usuario OR tp.jugador2_id = u.id_usuario)
        JOIN torneo_categorias tcat ON tp.categoria_id = tcat.id
        WHERE u.email LIKE '%@driveplus.temp' AND tp.torneo_id = 38
    """)).fetchall()

    print(f"\n{'=' * 70}")
    print("COINCIDENCIAS CON TEMP T38")
    print("=" * 70)
    
    for r in reales:
        r_id, r_user, r_email, r_rat, r_cat, r_nom, r_ape = r
        r_full = f"{r_nom} {r_ape}".strip()
        
        best = None
        best_score = 0
        for t in temps:
            t_id, t_nom, t_ape, t_rat, t_cat = t
            t_full = f"{t_nom} {t_ape}".strip()
            
            s_ape = sim(r_ape, t_ape)
            s_nom = sim(r_nom, t_nom)
            s_full = sim(r_full, t_full)
            score = max(s_full, (s_ape * 0.6 + s_nom * 0.4) if s_ape > 0.7 else 0)
            
            if score > best_score:
                best_score = score
                best = t
        
        if best and best_score >= 0.5:
            t_id, t_nom, t_ape, t_rat, t_cat = best
            pct = f"{best_score*100:.0f}%"
            print(f"\n  {pct} REAL: {r_nom} {r_ape} (ID={r_id}, user={r_user})")
            print(f"       TEMP: {t_nom} {t_ape} (ID={t_id}, {t_cat}, rating={t_rat})")
        else:
            print(f"\n  ❌ {r_nom} {r_ape} (ID={r_id}, user={r_user}) - sin match temp")
