"""Analizar duplicados que tienen parejas activas en ambas cuentas"""
import os, sys
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def similitud(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

print("=" * 80)
print("DUPLICADOS CON PAREJAS ACTIVAS (REQUIEREN MIGRACIÓN)")
print("=" * 80)

with engine.connect() as c:
    # Obtener todos los usuarios
    usuarios = c.execute(text("""
        SELECT u.id_usuario, u.nombre_usuario, u.email,
               COALESCE(p.nombre, '') as nombre, COALESCE(p.apellido, '') as apellido,
               u.rating, u.partidos_jugados
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        ORDER BY u.id_usuario
    """)).fetchall()
    
    # Separar temps y reales
    temps = [u for u in usuarios if ("@temp.com" in u[2] or "@driveplus.temp" in u[2])]
    reales = [u for u in usuarios if not ("@temp.com" in u[2] or "@driveplus.temp" in u[2])]
    
    # Buscar duplicados con alta similitud
    casos_criticos = []
    
    for temp in temps:
        temp_nombre = f"{temp[3]} {temp[4]}".strip()
        if not temp_nombre:
            continue
        
        for real in reales:
            real_nombre = f"{real[3]} {real[4]}".strip()
            if not real_nombre:
                continue
            
            sim = similitud(temp_nombre, real_nombre)
            
            if sim >= 0.90:  # 90%+ similitud
                # Ver parejas de ambos
                parejas_temp = c.execute(text("""
                    SELECT tp.id, t.id, t.nombre, tc.nombre as categoria
                    FROM torneos_parejas tp
                    JOIN torneos t ON tp.torneo_id = t.id
                    LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
                    WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
                    ORDER BY t.id
                """), {"uid": temp[0]}).fetchall()
                
                parejas_real = c.execute(text("""
                    SELECT tp.id, t.id, t.nombre, tc.nombre as categoria
                    FROM torneos_parejas tp
                    JOIN torneos t ON tp.torneo_id = t.id
                    LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
                    WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
                    ORDER BY t.id
                """), {"uid": real[0]}).fetchall()
                
                # Solo mostrar si ambos tienen parejas o si el temp tiene parejas
                if parejas_temp:
                    casos_criticos.append({
                        'temp': temp,
                        'real': real,
                        'sim': sim,
                        'parejas_temp': parejas_temp,
                        'parejas_real': parejas_real
                    })
    
    # Ordenar por similitud
    casos_criticos.sort(key=lambda x: -x['sim'])
    
    print(f"\nCASOS ENCONTRADOS: {len(casos_criticos)}\n")
    
    for caso in casos_criticos:
        temp = caso['temp']
        real = caso['real']
        sim = caso['sim']
        temp_nombre = f"{temp[3]} {temp[4]}".strip()
        
        print(f"{'=' * 80}")
        print(f"{int(sim*100)}% SIMILITUD - {temp_nombre}")
        print(f"{'=' * 80}")
        print(f"TEMP: ID={temp[0]}, user={temp[1]}, rating={temp[5]}, pj={temp[6]}")
        print(f"      Email: {temp[2]}")
        
        if caso['parejas_temp']:
            print(f"      Parejas ({len(caso['parejas_temp'])}):")
            for p in caso['parejas_temp']:
                print(f"        - Pareja {p[0]}: T{p[1]} ({p[2]}) - {p[3] or 'sin cat'}")
        else:
            print(f"      Sin parejas")
        
        print(f"\nREAL: ID={real[0]}, user={real[1]}, rating={real[5]}, pj={real[6]}")
        print(f"      Email: {real[2]}")
        
        if caso['parejas_real']:
            print(f"      Parejas ({len(caso['parejas_real'])}):")
            for p in caso['parejas_real']:
                print(f"        - Pareja {p[0]}: T{p[1]} ({p[2]}) - {p[3] or 'sin cat'}")
        else:
            print(f"      Sin parejas")
        
        # Sugerencia
        if caso['parejas_temp'] and not caso['parejas_real']:
            print(f"\n  💡 SUGERENCIA: Migrar parejas de TEMP → REAL y eliminar temp")
        elif caso['parejas_temp'] and caso['parejas_real']:
            print(f"\n  ⚠️  CRÍTICO: Ambos tienen parejas - revisar manualmente")
        
        print()

print("=" * 80)
