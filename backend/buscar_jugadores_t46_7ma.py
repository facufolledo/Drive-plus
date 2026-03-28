"""
Script para buscar jugadores del torneo 46 - 7ma
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from difflib import SequenceMatcher
from unicodedata import normalize as unicode_normalize

def normalizar_texto(texto):
    """Normaliza texto removiendo acentos y convirtiendo a minúsculas"""
    if not texto:
        return ""
    texto = unicode_normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return ' '.join(texto.lower().strip().split())

# Leer DATABASE_URL del archivo .env.production
env_file = os.path.join(os.path.dirname(__file__), '.env.production')
DATABASE_URL = None
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DATABASE_URL = line.split('=', 1)[1].strip().strip('"').strip("'")
                break

if not DATABASE_URL:
    print("❌ ERROR: Variable DATABASE_URL no encontrada en .env.production")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# Parejas del torneo 46 - 7ma
PAREJAS_T46_7MA = [
    {"j1": "Lucero Emiliano", "j2": "Folledo Facundo", "restricciones": {"viernes": [16,17,18,19,20,21,22,23,24], "sabado": [], "domingo": []}},
    {"j1": "Diaz Alvaro", "j2": "Montivero Federico", "restricciones": {"viernes": [19,20,21,22,23,24], "sabado": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19], "domingo": []}},
    {"j1": "Moreno Matías", "j2": "Moreno Cristian", "restricciones": {"viernes": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,22,23,24], "sabado": [19,20,21,22,23,24], "domingo": []}},
    {"j1": "Apostolo lucas", "j2": "Roldán Mariano", "restricciones": {"viernes": [17,18,19,20,21,22], "sabado": [], "domingo": []}},
    {"j1": "Barros Fabricio", "j2": "Cruz Mariano", "restricciones": {"viernes": [20,21,22,23,24], "sabado": [], "domingo": []}},
    {"j1": "Millicay Gustavo", "j2": "Heredia Ezequiel", "restricciones": {"viernes": [18], "sabado": [], "domingo": []}},
    {"j1": "Juin lucas", "j2": "López Tiago", "restricciones": {"viernes": [18,19,20,21,22,23], "sabado": [12,13,14,15,16,17,18,19,20,21,22,23,24], "domingo": []}},
    {"j1": "Yaryura Imanol", "j2": "Diaz Santi", "restricciones": {"viernes": [], "sabado": [], "domingo": []}},
    {"j1": "Bedini Esteban", "j2": "Johannesen Benicio", "restricciones": {"viernes": [14,15,16,17,18,19,20,21,22,23,24], "sabado": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16], "domingo": []}},
    {"j1": "Silva Joselin", "j2": "Aguilar Dilan", "restricciones": {"viernes": [0,1], "sabado": [14,15,16,17,18,19,20,21,22,23,24], "domingo": []}},
    {"j1": "Diaz Nazareno", "j2": "Salido Ismael", "restricciones": {"viernes": [], "sabado": [12,13,14,15,16,17,18,19,20,21,22,23,24], "domingo": []}},
    {"j1": "Romero Juan Pablo", "j2": "Romero Juan Pablo Jr", "restricciones": {"viernes": [19,20,21,22,23,24], "sabado": [], "domingo": []}},
    {"j1": "Brizuela Aron", "j2": "Moreno Valentín", "restricciones": {"viernes": [], "sabado": [], "domingo": []}},
    {"j1": "Alfaro axel", "j2": "Alfaro Matías", "restricciones": {"viernes": [18,19,20,21,22,23,24], "sabado": [], "domingo": []}},
    {"j1": "Bicet Diego", "j2": "Aguilar Marcelo", "restricciones": {"viernes": [15,16,17,18,19,20,21,22,23,24], "sabado": [], "domingo": []}},
    {"j1": "Mercado Agustín", "j2": "Zaracho cesar", "restricciones": {"viernes": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24], "sabado": [], "domingo": []}},
    {"j1": "Villarrubia Leonardo", "j2": "Ibañaz Alberto", "restricciones": {"viernes": [20,21,22,23,24], "sabado": [], "domingo": []}},
    {"j1": "Nieto mariano", "j2": "Olivera Federico", "restricciones": {"viernes": [], "sabado": [14,15,16,17,18,19,20,21,22,23,24], "domingo": []}},
    {"j1": "Aredes Martín", "j2": "Aredes Matías", "restricciones": {"viernes": [14,15,16,17,18,19,20,21], "sabado": [], "domingo": []}},
]

def similitud(texto1, texto2):
    return SequenceMatcher(None, texto1.lower(), texto2.lower()).ratio()

def buscar_jugador_similar(conn, nombre_completo):
    partes = nombre_completo.split()
    if len(partes) < 2:
        return []
    
    nombre = partes[0]
    apellido = " ".join(partes[1:])
    
    query = text("""
        SELECT 
            pu.id_usuario,
            pu.nombre,
            pu.apellido,
            u.email,
            u.nombre_usuario,
            c.nombre as categoria
        FROM perfil_usuarios pu
        INNER JOIN usuarios u ON pu.id_usuario = u.id_usuario
        LEFT JOIN categorias c ON u.id_categoria = c.id_categoria
        WHERE pu.nombre IS NOT NULL 
          AND pu.apellido IS NOT NULL
          AND u.email NOT LIKE '%@driveplus.temp%'
    """)
    
    result = conn.execute(query).fetchall()
    
    nombre_norm = normalizar_texto(nombre)
    apellido_norm = normalizar_texto(apellido)
    nombre_completo_norm = normalizar_texto(nombre_completo)
    
    matches = []
    for row in result:
        nombre_db_norm = normalizar_texto(row.nombre)
        apellido_db_norm = normalizar_texto(row.apellido)
        nombre_completo_db_norm = normalizar_texto(f"{row.nombre} {row.apellido}")
        nombre_completo_db_invertido_norm = normalizar_texto(f"{row.apellido} {row.nombre}")
        
        sim_completo = similitud(nombre_completo_norm, nombre_completo_db_norm)
        sim_completo_invertido = similitud(nombre_completo_norm, nombre_completo_db_invertido_norm)
        
        sim_nombre = similitud(nombre_norm, nombre_db_norm)
        sim_apellido = similitud(apellido_norm, apellido_db_norm)
        
        sim_nombre_inv = similitud(nombre_norm, apellido_db_norm)
        sim_apellido_inv = similitud(apellido_norm, nombre_db_norm)
        
        sim = max(
            sim_completo,
            sim_completo_invertido,
            (sim_nombre + sim_apellido) / 2,
            (sim_nombre_inv + sim_apellido_inv) / 2
        )
        
        if sim >= 0.7:
            invertido = sim_completo_invertido > sim_completo or (sim_nombre_inv + sim_apellido_inv) > (sim_nombre + sim_apellido)
            matches.append({
                "id_usuario": row.id_usuario,
                "nombre": row.nombre,
                "apellido": row.apellido,
                "email": row.email,
                "nombre_usuario": row.nombre_usuario,
                "categoria": row.categoria,
                "similitud": sim,
                "invertido": invertido
            })
    
    matches.sort(key=lambda x: x["similitud"], reverse=True)
    return matches[:3]

def main():
    print("=" * 80)
    print("BÚSQUEDA DE JUGADORES - TORNEO 46 - 7MA")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        torneo = conn.execute(text("SELECT id, nombre FROM torneos WHERE id = 46")).fetchone()
        if not torneo:
            print("❌ ERROR: Torneo 46 no existe")
            return
        
        print(f"✅ Torneo encontrado: {torneo.nombre}")
        print()
        
        resultados = []
        
        for i, pareja in enumerate(PAREJAS_T46_7MA, 1):
            print(f"\n{'='*80}")
            print(f"PAREJA {i}: {pareja['j1']} + {pareja['j2']}")
            print(f"{'='*80}")
            
            print(f"\n🔍 Buscando J1: {pareja['j1']}")
            matches_j1 = buscar_jugador_similar(conn, pareja['j1'])
            
            if matches_j1:
                print(f"   ✅ Encontrados {len(matches_j1)} match(es):")
                for m in matches_j1:
                    inv = " ⚠️ INVERTIDO" if m['invertido'] else ""
                    print(f"      - ID {m['id_usuario']}: {m['nombre']} {m['apellido']} ({m['categoria']}){inv} - {m['similitud']*100:.0f}%")
            else:
                print(f"   ❌ NO encontrado")
            
            print(f"\n🔍 Buscando J2: {pareja['j2']}")
            matches_j2 = buscar_jugador_similar(conn, pareja['j2'])
            
            if matches_j2:
                print(f"   ✅ Encontrados {len(matches_j2)} match(es):")
                for m in matches_j2:
                    inv = " ⚠️ INVERTIDO" if m['invertido'] else ""
                    print(f"      - ID {m['id_usuario']}: {m['nombre']} {m['apellido']} ({m['categoria']}){inv} - {m['similitud']*100:.0f}%")
            else:
                print(f"   ❌ NO encontrado")
            
            resultados.append({
                "pareja_num": i,
                "j1_nombre": pareja['j1'],
                "j2_nombre": pareja['j2'],
                "j1_matches": matches_j1,
                "j2_matches": matches_j2,
                "restricciones": pareja['restricciones']
            })
        
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        
        encontrados_j1 = sum(1 for r in resultados if r['j1_matches'])
        encontrados_j2 = sum(1 for r in resultados if r['j2_matches'])
        
        print(f"✅ Jugadores 1 encontrados: {encontrados_j1}/{len(PAREJAS_T46_7MA)}")
        print(f"✅ Jugadores 2 encontrados: {encontrados_j2}/{len(PAREJAS_T46_7MA)}")
        
        no_encontrados = []
        for r in resultados:
            if not r['j1_matches']:
                no_encontrados.append(r['j1_nombre'])
            if not r['j2_matches']:
                no_encontrados.append(r['j2_nombre'])
        
        if no_encontrados:
            print(f"\n⚠️  Jugadores NO encontrados ({len(no_encontrados)}):")
            for nombre in no_encontrados:
                print(f"   - {nombre}")
        
        print("\n" + "=" * 80)
        print("SIGUIENTE PASO:")
        print("Revisa los matches y confirma los IDs correctos.")
        print("Luego ejecutaremos el script de inscripción.")
        print("=" * 80)

if __name__ == "__main__":
    main()
