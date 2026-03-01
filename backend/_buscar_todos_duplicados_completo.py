"""Buscar TODOS los duplicados comparando temps con reales por nombre y apellido"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from difflib import SequenceMatcher

engine = create_engine(os.getenv("DATABASE_URL"))

def similitud(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

with engine.connect() as conn:
    print("=== BUSCANDO DUPLICADOS TEMPS VS REALES ===\n")
    
    # Obtener todos los temps
    temps = conn.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email, u.rating, u.partidos_jugados
        FROM usuarios u
        JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.email LIKE '%@driveplus.temp' OR u.email LIKE '%@temp.com'
        ORDER BY u.id_usuario
    """)).fetchall()
    
    # Obtener todos los reales
    reales = conn.execute(text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.email, u.rating, u.partidos_jugados
        FROM usuarios u
        JOIN perfil_usuarios p ON p.id_usuario = u.id_usuario
        WHERE u.email NOT LIKE '%@driveplus.temp' AND u.email NOT LIKE '%@temp.com'
        ORDER BY u.id_usuario
    """)).fetchall()
    
    print(f"Temps: {len(temps)}, Reales: {len(reales)}\n")
    
    duplicados_encontrados = []
    
    for temp in temps:
        temp_nombre = (temp[1] or "").strip()
        temp_apellido = (temp[2] or "").strip()
        
        if not temp_nombre or not temp_apellido:
            continue
        
        for real in reales:
            real_nombre = (real[1] or "").strip()
            real_apellido = (real[2] or "").strip()
            
            if not real_nombre or not real_apellido:
                continue
            
            # Calcular similitud
            sim_nombre = similitud(temp_nombre, real_nombre)
            sim_apellido = similitud(temp_apellido, real_apellido)
            sim_total = (sim_nombre + sim_apellido) / 2
            
            if sim_total >= 0.80:  # 80% de similitud
                duplicados_encontrados.append({
                    "temp_id": temp[0],
                    "temp_nombre": f"{temp_nombre} {temp_apellido}",
                    "temp_pj": temp[5],
                    "real_id": real[0],
                    "real_nombre": f"{real_nombre} {real_apellido}",
                    "real_pj": real[5],
                    "similitud": sim_total
                })
    
    # Ordenar por similitud
    duplicados_encontrados.sort(key=lambda x: x["similitud"], reverse=True)
    
    print(f"=== DUPLICADOS ENCONTRADOS ({len(duplicados_encontrados)}) ===\n")
    
    for dup in duplicados_encontrados:
        print(f"{int(dup['similitud']*100)}% SIMILITUD")
        print(f"[TEMP] {dup['temp_nombre']} (ID={dup['temp_id']}, PJ={dup['temp_pj']})")
        print(f"[REAL] {dup['real_nombre']} (ID={dup['real_id']}, PJ={dup['real_pj']})")
        print()
    
    print("✅ Búsqueda completada")
