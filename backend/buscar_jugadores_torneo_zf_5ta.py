"""
Script para buscar jugadores del torneo ZF 5ta y preparar asignación de puntos
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
# Cargar .env desde el directorio del script
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.production'))

from sqlalchemy import create_engine, text
from difflib import SequenceMatcher
from unicodedata import normalize as unicode_normalize

def normalizar_texto(texto):
    """Normaliza texto removiendo acentos y convirtiendo a minúsculas"""
    if not texto:
        return ""
    # Remover acentos
    texto = unicode_normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    # Minúsculas y quitar espacios extra
    return ' '.join(texto.lower().strip().split())

# Obtener DATABASE_URL del entorno
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: Variable DATABASE_URL no encontrada")
    print("   Asegúrate de tener el archivo .env.production configurado")
    print(f"   Buscando en: {os.path.join(os.path.dirname(__file__), '.env.production')}")
    sys.exit(1)

# Jugadores del torneo ZF 5ta con sus puntos
JUGADORES_TORNEO_ZF = [
    {"nombre": "Loto Juan", "puntos": 1000, "fase": "campeon"},
    {"nombre": "Navarro Martín", "puntos": 1000, "fase": "campeon"},
    {"nombre": "Calderón Juan", "puntos": 600, "fase": "semis"},
    {"nombre": "Villegas Ignacio", "puntos": 600, "fase": "semis"},
    {"nombre": "Nani tomas", "puntos": 600, "fase": "semis"},
    {"nombre": "Ábrego maxi", "puntos": 600, "fase": "semis"},
    {"nombre": "Castro Joel", "puntos": 400, "fase": "cuartos"},
    {"nombre": "Aguilar Gonzalo", "puntos": 400, "fase": "cuartos"},
    {"nombre": "Farran Bastian", "puntos": 400, "fase": "cuartos"},
    {"nombre": "Montiel nazareno", "puntos": 400, "fase": "cuartos"},
    {"nombre": "Diaz mateo", "puntos": 400, "fase": "cuartos"},
    {"nombre": "Sosa Bautista", "puntos": 400, "fase": "cuartos"},
    {"nombre": "Nieto Axel", "puntos": 100, "fase": "zona"},
    {"nombre": "Tello sergio", "puntos": 100, "fase": "zona"},
    {"nombre": "Casas Miguel", "puntos": 100, "fase": "zona"},
    {"nombre": "Brizuela juaquin", "puntos": 100, "fase": "zona"},
    {"nombre": "Oliva Bautista", "puntos": 100, "fase": "zona"},
    {"nombre": "Peñaloza Nicolás", "puntos": 100, "fase": "zona"},
]

engine = create_engine(DATABASE_URL)

def normalizar_nombre(nombre):
    """Normaliza nombre para búsqueda"""
    return nombre.lower().strip()

def similitud(texto1, texto2):
    """Calcular similitud entre dos textos (0.0 a 1.0)"""
    return SequenceMatcher(None, texto1.lower(), texto2.lower()).ratio()

def buscar_jugador_similar(conn, nombre_completo):
    """Busca jugadores similares en la base de datos"""
    partes = nombre_completo.split()
    
    if len(partes) < 2:
        return []
    
    # Separar nombre y apellido
    nombre = partes[0]
    apellido = " ".join(partes[1:])
    
    # Traer TODOS los usuarios de perfil_usuarios (sin filtro en SQL)
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
    
    # Normalizar el nombre buscado
    nombre_norm = normalizar_texto(nombre)
    apellido_norm = normalizar_texto(apellido)
    nombre_completo_norm = normalizar_texto(nombre_completo)
    
    # Filtrar por similitud en Python
    matches = []
    for row in result:
        nombre_db_norm = normalizar_texto(row.nombre)
        apellido_db_norm = normalizar_texto(row.apellido)
        nombre_completo_db_norm = normalizar_texto(f"{row.nombre} {row.apellido}")
        nombre_completo_db_invertido_norm = normalizar_texto(f"{row.apellido} {row.nombre}")
        
        # Calcular similitud del nombre completo (normal e invertido)
        sim_completo = similitud(nombre_completo_norm, nombre_completo_db_norm)
        sim_completo_invertido = similitud(nombre_completo_norm, nombre_completo_db_invertido_norm)
        
        # Calcular similitud de nombre y apellido por separado (normal)
        sim_nombre = similitud(nombre_norm, nombre_db_norm)
        sim_apellido = similitud(apellido_norm, apellido_db_norm)
        
        # Calcular similitud de nombre y apellido por separado (invertido)
        sim_nombre_inv = similitud(nombre_norm, apellido_db_norm)
        sim_apellido_inv = similitud(apellido_norm, nombre_db_norm)
        
        # Usar la mejor similitud entre todas las combinaciones
        sim = max(
            sim_completo,
            sim_completo_invertido,
            (sim_nombre + sim_apellido) / 2,
            (sim_nombre_inv + sim_apellido_inv) / 2
        )
        
        # Solo incluir si la similitud es >= 70%
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
                "sim_nombre": sim_nombre_inv if invertido else sim_nombre,
                "sim_apellido": sim_apellido_inv if invertido else sim_apellido,
                "invertido": invertido
            })
    
    # Ordenar por similitud descendente
    matches.sort(key=lambda x: x["similitud"], reverse=True)
    
    # Limitar a top 3 matches
    return matches[:3]

def main():
    print("=" * 80)
    print("BÚSQUEDA DE JUGADORES - TORNEO ZF 5TA")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        encontrados = []
        no_encontrados = []
        
        for jugador_data in JUGADORES_TORNEO_ZF:
            nombre = jugador_data["nombre"]
            puntos = jugador_data["puntos"]
            fase = jugador_data["fase"]
            
            print(f"\n🔍 Buscando: {nombre} ({puntos} pts - {fase})")
            print("-" * 80)
            
            matches = buscar_jugador_similar(conn, nombre)
            
            if matches:
                print(f"   ✅ Encontrados {len(matches)} match(es):")
                for match in matches:
                    invertido_txt = " ⚠️ INVERTIDO" if match.get('invertido') else ""
                    print(f"      - ID: {match['id_usuario']}{invertido_txt}")
                    print(f"        Nombre: {match['nombre']} {match['apellido']}")
                    print(f"        Email: {match['email']}")
                    print(f"        Usuario: {match['nombre_usuario']}")
                    print(f"        Categoría: {match['categoria']}")
                    print(f"        Similitud: {match['similitud']*100:.1f}% (nombre: {match['sim_nombre']*100:.0f}%, apellido: {match['sim_apellido']*100:.0f}%)")
                    print()
                
                encontrados.append({
                    "nombre_buscado": nombre,
                    "puntos": puntos,
                    "fase": fase,
                    "matches": matches
                })
            else:
                print(f"   ❌ NO encontrado en la base de datos")
                no_encontrados.append(jugador_data)
        
        # Resumen
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"\n✅ Encontrados: {len(encontrados)}")
        print(f"❌ No encontrados: {len(no_encontrados)}")
        
        if no_encontrados:
            print("\n⚠️  Jugadores NO encontrados en la base de datos:")
            for j in no_encontrados:
                print(f"   - {j['nombre']} ({j['puntos']} pts)")
            print("\n   Estos jugadores necesitarán ser creados o verificados manualmente.")
        
        print("\n" + "=" * 80)
        print("SIGUIENTE PASO:")
        print("Revisa los matches encontrados y confirma si son correctos.")
        print("Luego ejecutaremos el script de asignación de puntos.")
        print("=" * 80)

if __name__ == "__main__":
    main()
