"""Buscar usuarios duplicados comparando TODOS contra TODOS
Encuentra usuarios con nombres muy parecidos que podrían ser la misma persona
"""
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
    # Todos los usuarios
    usuarios = c.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email,
               COALESCE(p.nombre, '') as nombre, COALESCE(p.apellido, '') as apellido,
               u.rating, u.partidos_jugados, u.password_hash
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        ORDER BY u.id_usuario
    """)).fetchall()

    print(f"Comparando {len(usuarios)} usuarios...")
    print()

    UMBRAL = 0.80  # similitud mínima (más alto = más estricto)
    matches = []

    # Comparar cada usuario con todos los demás
    for i, u1 in enumerate(usuarios):
        u1_nombre = f"{u1[3]} {u1[4]}".strip()
        if not u1_nombre:
            continue
        
        for u2 in usuarios[i+1:]:  # Solo comparar con usuarios posteriores (evitar duplicados)
            u2_nombre = f"{u2[3]} {u2[4]}".strip()
            if not u2_nombre:
                continue
            
            # Comparar nombre completo
            sim_full = similitud(u1_nombre, u2_nombre)
            
            # Comparar apellido solo (más peso)
            sim_ape = similitud(u1[4], u2[4]) if u1[4] and u2[4] else 0
            
            # Comparar nombre solo
            sim_nom = similitud(u1[3], u2[3]) if u1[3] and u2[3] else 0
            
            # Score combinado: apellido exacto + nombre parecido es muy probable
            if sim_ape > 0.90 and sim_nom > 0.60:
                score = max(sim_full, (sim_ape + sim_nom) / 2)
            else:
                score = sim_full
            
            if score >= UMBRAL:
                matches.append((score, u1, u1_nombre, u2, u2_nombre))

    # Ordenar por score
    matches.sort(key=lambda x: -x[0])
    
    print(f"{'=' * 90}")
    print(f"POSIBLES DUPLICADOS ENCONTRADOS ({len(matches)})")
    print(f"{'=' * 90}")
    
    for score, u1, u1_nombre, u2, u2_nombre in matches:
        # Determinar tipo de cada usuario
        u1_tipo = "TEMP" if ("@driveplus.temp" in u1[2] or "@temp.com" in u1[2]) else "REAL"
        u2_tipo = "TEMP" if ("@driveplus.temp" in u2[2] or "@temp.com" in u2[2]) else "REAL"
        
        # Ver en qué torneos están
        u1_torneos = c.execute(text("""
            SELECT DISTINCT tp.torneo_id FROM torneos_parejas tp
            WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
            ORDER BY tp.torneo_id
        """), {"uid": u1[0]}).fetchall()
        u1_t = ", ".join([f"T{t[0]}" for t in u1_torneos]) if u1_torneos else "-"
        
        u2_torneos = c.execute(text("""
            SELECT DISTINCT tp.torneo_id FROM torneos_parejas tp
            WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
            ORDER BY tp.torneo_id
        """), {"uid": u2[0]}).fetchall()
        u2_t = ", ".join([f"T{t[0]}" for t in u2_torneos]) if u2_torneos else "-"
        
        pct = f"{score*100:.0f}%"
        
        print(f"\n  {pct} SIMILITUD")
        print(f"    [{u1_tipo}] {u1_nombre} (ID={u1[0]}, user={u1[1]}, rating={u1[5]}, pj={u1[6]}) [{u1_t}]")
        print(f"    [{u2_tipo}] {u2_nombre} (ID={u2[0]}, user={u2[1]}, rating={u2[5]}, pj={u2[6]}) [{u2_t}]")

print("\n✅ Búsqueda completa")
