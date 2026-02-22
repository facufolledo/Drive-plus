"""Buscar usuarios temp que coincidan (o se parezcan) a usuarios reales (Firebase).
Usuarios reales = contraseña vacía/null (autenticados por Firebase).
Usuarios temp = email @driveplus.temp con hash 'temp_no_login'.
Compara TODOS los temp con TODOS los reales usando similitud de nombre."""
import os, sys
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def similitud(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

with engine.connect() as c:
    # Todos los temp
    temps = c.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email, 
               COALESCE(p.nombre, '') as nombre, COALESCE(p.apellido, '') as apellido,
               u.rating, u.partidos_jugados
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.email LIKE '%@driveplus.temp'
        ORDER BY COALESCE(p.apellido, ''), COALESCE(p.nombre, '')
    """)).fetchall()

    # Todos los reales (contraseña vacía/null = Firebase)
    reales = c.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email,
               COALESCE(p.nombre, '') as nombre, COALESCE(p.apellido, '') as apellido,
               u.rating, u.partidos_jugados
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.email NOT LIKE '%@driveplus.temp'
        AND (u.password_hash IS NULL OR u.password_hash = '' OR u.password_hash = 'null')
        ORDER BY COALESCE(p.apellido, ''), COALESCE(p.nombre, '')
    """)).fetchall()

    print(f"Total temp: {len(temps)}")
    print(f"Total reales (Firebase): {len(reales)}")
    print()

    # Comparar cada temp con cada real
    UMBRAL = 0.65  # similitud mínima para reportar
    matches = []

    for t in temps:
        t_nombre = f"{t[3]} {t[4]}".strip()
        if not t_nombre:
            continue
        
        mejores = []
        for r in reales:
            r_nombre = f"{r[3]} {r[4]}".strip()
            if not r_nombre:
                continue
            
            # Comparar nombre completo
            sim_full = similitud(t_nombre, r_nombre)
            
            # Comparar apellido solo (más peso)
            sim_ape = similitud(t[4], r[4]) if t[4] and r[4] else 0
            
            # Comparar nombre solo
            sim_nom = similitud(t[3], r[3]) if t[3] and r[3] else 0
            
            # Score combinado: apellido exacto + nombre parecido es muy probable
            if sim_ape > 0.85 and sim_nom > 0.5:
                score = max(sim_full, (sim_ape + sim_nom) / 2)
            else:
                score = sim_full
            
            if score >= UMBRAL:
                mejores.append((score, r, r_nombre))
        
        if mejores:
            mejores.sort(key=lambda x: -x[0])
            best = mejores[0]
            matches.append((t, t_nombre, best))

    # Mostrar resultados ordenados por score
    matches.sort(key=lambda x: -x[2][0])
    
    print(f"{'=' * 80}")
    print(f"COINCIDENCIAS ENCONTRADAS ({len(matches)})")
    print(f"{'=' * 80}")
    
    for t, t_nombre, (score, r, r_nombre) in matches:
        # Verificar si el temp está en torneo 38
        en_t38 = c.execute(text("""
            SELECT COUNT(*) FROM torneos_parejas 
            WHERE torneo_id = 38 AND (jugador1_id = :tid OR jugador2_id = :tid)
        """), {"tid": t[0]}).fetchone()[0]
        
        t38_tag = " [T38]" if en_t38 > 0 else ""
        pct = f"{score*100:.0f}%"
        
        print(f"\n  {pct} | TEMP: {t_nombre} (ID={t[0]}, rating={t[5]}, pj={t[6]}){t38_tag}")
        print(f"       | REAL: {r_nombre} (ID={r[0]}, user={r[1]}, rating={r[5]}, pj={r[6]})")
