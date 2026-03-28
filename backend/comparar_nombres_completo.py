#!/usr/bin/env python3
"""
Comparar nombres y apellidos de todos los usuarios con perfil_usuarios
Busca duplicados potenciales por similitud de nombres
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from difflib import SequenceMatcher

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

def similitud(a, b):
    """Calcula similitud entre dos strings (0-1)"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def main():
    s = Session()
    try:
        print("=" * 80)
        print("COMPARAR NOMBRES Y APELLIDOS - TODOS LOS USUARIOS")
        print("=" * 80)

        # Obtener todos los usuarios con sus perfiles
        usuarios = s.execute(text("""
            SELECT 
                u.id_usuario,
                u.nombre_usuario,
                u.email,
                u.rating,
                COALESCE(p.nombre, '') as nombre,
                COALESCE(p.apellido, '') as apellido,
                CASE 
                    WHEN u.email LIKE '%@driveplus.temp' THEN 'TEMP'
                    WHEN u.password_hash IS NULL OR u.password_hash = '' THEN 'FIREBASE'
                    ELSE 'LOCAL'
                END as tipo_cuenta
            FROM usuarios u
            LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
            ORDER BY p.apellido, p.nombre
        """)).fetchall()

        print(f"\n📊 Total usuarios: {len(usuarios)}\n")

        # Buscar similitudes
        matches = []
        
        for i, u1 in enumerate(usuarios):
            id1, user1, email1, rat1, nom1, ape1, tipo1 = u1
            full1 = f"{nom1} {ape1}".strip()
            
            if not full1:  # Skip usuarios sin perfil
                continue
            
            for u2 in usuarios[i+1:]:
                id2, user2, email2, rat2, nom2, ape2, tipo2 = u2
                full2 = f"{nom2} {ape2}".strip()
                
                if not full2:
                    continue
                
                # Calcular similitudes
                sim_apellido = similitud(ape1, ape2)
                sim_nombre = similitud(nom1, nom2)
                sim_completo = similitud(full1, full2)
                
                # Criterios de match
                score = 0
                razon = ""
                
                # Apellido muy similar + nombre similar
                if sim_apellido >= 0.85 and sim_nombre >= 0.7:
                    score = (sim_apellido + sim_nombre) / 2
                    razon = "nombre+apellido"
                
                # Solo apellido muy similar (mismo apellido, nombres diferentes)
                elif sim_apellido >= 0.85:
                    score = sim_apellido * 0.75
                    razon = f"solo apellido ({nom1} vs {nom2})"
                
                # Nombre completo similar
                elif sim_completo >= 0.75:
                    score = sim_completo
                    razon = "nombre completo"
                
                # Nombre exacto, apellido diferente
                elif sim_nombre >= 0.9 and sim_apellido >= 0.5:
                    score = (sim_nombre + sim_apellido) / 2
                    razon = "nombre similar, apellido parcial"
                
                if score >= 0.65:  # Umbral de similitud
                    matches.append((score, u1, u2, razon, sim_apellido, sim_nombre, sim_completo))

        # Ordenar por score descendente
        matches.sort(key=lambda x: -x[0])

        print("=" * 80)
        print(f"COINCIDENCIAS ENCONTRADAS: {len(matches)}")
        print("=" * 80)

        # Agrupar por tipo de match
        temp_vs_real = []
        temp_vs_temp = []
        real_vs_real = []
        
        for match in matches:
            score, u1, u2, razon, sim_ape, sim_nom, sim_full = match
            tipo1 = u1[6]
            tipo2 = u2[6]
            
            if (tipo1 == 'TEMP' and tipo2 in ['FIREBASE', 'LOCAL']) or \
               (tipo2 == 'TEMP' and tipo1 in ['FIREBASE', 'LOCAL']):
                temp_vs_real.append(match)
            elif tipo1 == 'TEMP' and tipo2 == 'TEMP':
                temp_vs_temp.append(match)
            else:
                real_vs_real.append(match)

        # Mostrar TEMP vs REAL (más importante)
        if temp_vs_real:
            print(f"\n🔥 TEMP vs REAL ({len(temp_vs_real)} matches)")
            print("=" * 80)
            for score, u1, u2, razon, sim_ape, sim_nom, sim_full in temp_vs_real:
                id1, user1, email1, rat1, nom1, ape1, tipo1 = u1
                id2, user2, email2, rat2, nom2, ape2, tipo2 = u2
                
                pct = f"{score*100:.0f}%"
                print(f"\n  {pct} [{razon}]")
                print(f"    Similitud: apellido={sim_ape:.2f}, nombre={sim_nom:.2f}, completo={sim_full:.2f}")
                
                if tipo1 == 'TEMP':
                    print(f"    TEMP: {nom1} {ape1} (ID={id1}, user={user1}, rating={rat1})")
                    print(f"    REAL: {nom2} {ape2} (ID={id2}, user={user2}, rating={rat2}, {tipo2})")
                else:
                    print(f"    REAL: {nom1} {ape1} (ID={id1}, user={user1}, rating={rat1}, {tipo1})")
                    print(f"    TEMP: {nom2} {ape2} (ID={id2}, user={user2}, rating={rat2})")

        # Mostrar REAL vs REAL
        if real_vs_real:
            print(f"\n\n👥 REAL vs REAL ({len(real_vs_real)} matches)")
            print("=" * 80)
            for score, u1, u2, razon, sim_ape, sim_nom, sim_full in real_vs_real[:10]:  # Top 10
                id1, user1, email1, rat1, nom1, ape1, tipo1 = u1
                id2, user2, email2, rat2, nom2, ape2, tipo2 = u2
                
                pct = f"{score*100:.0f}%"
                print(f"\n  {pct} [{razon}]")
                print(f"    Similitud: apellido={sim_ape:.2f}, nombre={sim_nom:.2f}, completo={sim_full:.2f}")
                print(f"    U1: {nom1} {ape1} (ID={id1}, user={user1}, rating={rat1}, {tipo1})")
                print(f"    U2: {nom2} {ape2} (ID={id2}, user={user2}, rating={rat2}, {tipo2})")

        # Mostrar TEMP vs TEMP
        if temp_vs_temp:
            print(f"\n\n🔄 TEMP vs TEMP ({len(temp_vs_temp)} matches)")
            print("=" * 80)
            for score, u1, u2, razon, sim_ape, sim_nom, sim_full in temp_vs_temp[:10]:  # Top 10
                id1, user1, email1, rat1, nom1, ape1, tipo1 = u1
                id2, user2, email2, rat2, nom2, ape2, tipo2 = u2
                
                pct = f"{score*100:.0f}%"
                print(f"\n  {pct} [{razon}]")
                print(f"    Similitud: apellido={sim_ape:.2f}, nombre={sim_nom:.2f}, completo={sim_full:.2f}")
                print(f"    T1: {nom1} {ape1} (ID={id1}, user={user1}, rating={rat1})")
                print(f"    T2: {nom2} {ape2} (ID={id2}, user={user2}, rating={rat2})")

        print("\n" + "=" * 80)
        print(f"RESUMEN:")
        print(f"  TEMP vs REAL: {len(temp_vs_real)}")
        print(f"  REAL vs REAL: {len(real_vs_real)}")
        print(f"  TEMP vs TEMP: {len(temp_vs_temp)}")
        print(f"  TOTAL: {len(matches)}")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
