"""Buscar temp del T38 que coincidan con usuarios reales.
Compara por perfil_usuarios (nombre, apellido) con similitud flexible:
- Match por apellido solo
- Match por nombre solo  
- Match por nombre completo
Reales = password_hash vacío/null (Firebase auth)
"""
import os, sys
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def sim(a, b):
    if not a or not b: return 0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

with engine.connect() as c:
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
        ORDER BY apellido, nombre
    """)).fetchall()

    # Reales (Firebase)
    reales = c.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, COALESCE(p.nombre,'') as nombre,
               COALESCE(p.apellido,'') as apellido, u.rating, u.email
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.email NOT LIKE '%@driveplus.temp'
        AND (u.password_hash IS NULL OR u.password_hash = '' OR u.password_hash = 'null')
    """)).fetchall()

    print(f"Temp T38: {len(temps)}, Reales Firebase: {len(reales)}")
    print(f"\n{'='*80}")
    
    matches = []
    for t in temps:
        t_id, t_nom, t_ape, t_rat, t_cat = t
        t_full = f"{t_nom} {t_ape}".strip()
        
        for r in reales:
            r_id, r_user, r_nom, r_ape, r_rat, r_email = r
            if r_id == t_id: continue
            
            r_full = f"{r_nom} {r_ape}".strip()
            
            # Calcular similitudes
            sim_ape = sim(t_ape, r_ape)
            sim_nom = sim(t_nom, r_nom)
            sim_full = sim(t_full, r_full)
            
            # Criterios de match
            score = 0
            reason = ""
            
            # Apellido exacto o muy parecido
            if sim_ape >= 0.85:
                if sim_nom >= 0.7:
                    score = max(sim_full, (sim_ape + sim_nom) / 2)
                    reason = "nombre+apellido"
                else:
                    score = sim_ape * 0.8  # solo apellido
                    reason = f"solo apellido ({t_nom} vs {r_nom})"
            
            # Nombre exacto, apellido diferente (raro pero posible)
            elif sim_nom >= 0.9 and sim_ape >= 0.5:
                score = (sim_nom + sim_ape) / 2
                reason = f"nombre similar, apellido parcial"
            
            # Full name match
            elif sim_full >= 0.75:
                score = sim_full
                reason = "nombre completo"
            
            if score >= 0.6:
                matches.append((score, t, r, reason))
    
    # Ordenar y mostrar
    matches.sort(key=lambda x: -x[0])
    
    # Eliminar duplicados (mismo temp, quedarse con el mejor match)
    seen_temps = set()
    unique = []
    for m in matches:
        t_id = m[1][0]
        if t_id not in seen_temps:
            seen_temps.add(t_id)
            unique.append(m)
    
    print(f"COINCIDENCIAS ({len(unique)} temp con match)")
    print(f"{'='*80}")
    
    for score, t, r, reason in unique:
        t_id, t_nom, t_ape, t_rat, t_cat = t
        r_id, r_user, r_nom, r_ape, r_rat, r_email = r
        pct = f"{score*100:.0f}%"
        print(f"\n  {pct} [{reason}]")
        print(f"    TEMP: {t_nom} {t_ape} (ID={t_id}, {t_cat}, rating={t_rat})")
        print(f"    REAL: {r_nom} {r_ape} (ID={r_id}, user={r_user}, rating={r_rat})")
