"""Eliminar usuarios temp que tienen duplicados 100% con usuarios reales"""
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
print("BUSCANDO TEMPS CON DUPLICADOS 100% EN USUARIOS REALES")
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
    
    print(f"\nTotal usuarios: {len(usuarios)}")
    print(f"Temps: {len(temps)}")
    print(f"Reales: {len(reales)}")
    
    # Buscar duplicados 100%
    duplicados_100 = []
    
    for temp in temps:
        temp_nombre = f"{temp[3]} {temp[4]}".strip()
        if not temp_nombre:
            continue
        
        for real in reales:
            real_nombre = f"{real[3]} {real[4]}".strip()
            if not real_nombre:
                continue
            
            sim = similitud(temp_nombre, real_nombre)
            
            if sim >= 0.99:  # 99%+ = prácticamente idéntico
                duplicados_100.append((temp, real, sim))
                break  # Solo el primer match
    
    print(f"\n{'=' * 80}")
    print(f"DUPLICADOS 100% ENCONTRADOS: {len(duplicados_100)}")
    print(f"{'=' * 80}")
    
    temps_a_eliminar = []
    
    for temp, real, sim in duplicados_100:
        temp_nombre = f"{temp[3]} {temp[4]}".strip()
        real_nombre = f"{real[3]} {real[4]}".strip()
        
        # Ver si el temp está en alguna pareja
        parejas_temp = c.execute(text("""
            SELECT tp.id, t.id, t.nombre
            FROM torneos_parejas tp
            JOIN torneos t ON tp.torneo_id = t.id
            WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
        """), {"uid": temp[0]}).fetchall()
        
        # Ver si el real está en alguna pareja
        parejas_real = c.execute(text("""
            SELECT tp.id, t.id, t.nombre
            FROM torneos_parejas tp
            JOIN torneos t ON tp.torneo_id = t.id
            WHERE tp.jugador1_id = :uid OR tp.jugador2_id = :uid
        """), {"uid": real[0]}).fetchall()
        
        print(f"\n{int(sim*100)}% - {temp_nombre}")
        print(f"  TEMP: ID={temp[0]}, user={temp[1]}, rating={temp[5]}, pj={temp[6]}")
        print(f"        Parejas: {len(parejas_temp)} - {[f'T{p[1]}' for p in parejas_temp]}")
        print(f"  REAL: ID={real[0]}, user={real[1]}, rating={real[5]}, pj={real[6]}")
        print(f"        Parejas: {len(parejas_real)} - {[f'T{p[1]}' for p in parejas_real]}")
        
        # Solo eliminar si el temp NO está en ninguna pareja
        if not parejas_temp:
            temps_a_eliminar.append(temp[0])
            print(f"  ✓ Marcado para eliminar (sin parejas)")
        else:
            print(f"  ⚠ NO se eliminará (tiene parejas activas)")
    
    # Eliminar temps sin parejas
    if temps_a_eliminar:
        print(f"\n{'=' * 80}")
        print(f"ELIMINANDO {len(temps_a_eliminar)} USUARIOS TEMP SIN PAREJAS")
        print(f"{'=' * 80}")
        
        for uid in temps_a_eliminar:
            # Eliminar perfil
            c.execute(text("DELETE FROM perfil_usuarios WHERE id_usuario = :uid"), {"uid": uid})
            # Eliminar usuario
            c.execute(text("DELETE FROM usuarios WHERE id_usuario = :uid"), {"uid": uid})
            print(f"  ✓ Eliminado usuario {uid}")
        
        c.commit()
        print(f"\n✅ {len(temps_a_eliminar)} usuarios temp eliminados")
    else:
        print(f"\n⚠ No hay temps para eliminar (todos tienen parejas activas)")

print("\n" + "=" * 80)
