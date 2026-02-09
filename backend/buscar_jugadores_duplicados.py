"""
Buscar jugadores duplicados o similares comparando nombres y apellidos en perfil_usuarios
Usa fuzzy matching para detectar nombres parecidos
"""

import sys
import os
from unicodedata import normalize
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def normalizar_texto(texto):
    """Normalizar texto para comparación (sin acentos, minúsculas, sin espacios extra)"""
    if not texto:
        return ""
    # Remover acentos
    texto = normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    # Minúsculas y quitar espacios extra
    return ' '.join(texto.lower().strip().split())

def similitud(texto1, texto2):
    """Calcular similitud entre dos textos (0.0 a 1.0)"""
    return SequenceMatcher(None, texto1, texto2).ratio()

print("🔍 Buscando jugadores duplicados o similares en perfil_usuarios...")
print("=" * 80)

# Umbral de similitud (0.85 = 85% similar)
UMBRAL_SIMILITUD = 0.85

with engine.connect() as conn:
    # Obtener todos los perfiles
    query = text("""
        SELECT 
            pu.id_usuario,
            pu.nombre,
            pu.apellido,
            u.email,
            u.nombre_usuario,
            u.rating,
            u.partidos_jugados,
            c.nombre as categoria
        FROM perfil_usuarios pu
        INNER JOIN usuarios u ON pu.id_usuario = u.id_usuario
        LEFT JOIN categorias c ON u.id_categoria = c.id_categoria
        ORDER BY pu.apellido, pu.nombre
    """)
    
    perfiles = conn.execute(query).fetchall()
    
    # Convertir a lista de diccionarios
    jugadores = []
    for perfil in perfiles:
        jugadores.append({
            'id_usuario': perfil.id_usuario,
            'nombre': perfil.nombre,
            'apellido': perfil.apellido,
            'nombre_norm': normalizar_texto(perfil.nombre),
            'apellido_norm': normalizar_texto(perfil.apellido),
            'nombre_completo_norm': normalizar_texto(f"{perfil.nombre} {perfil.apellido}"),
            'email': perfil.email,
            'nombre_usuario': perfil.nombre_usuario,
            'rating': perfil.rating,
            'partidos_jugados': perfil.partidos_jugados,
            'categoria': perfil.categoria
        })
    
    # Buscar similitudes
    grupos_similares = []
    procesados = set()
    
    for i, jugador1 in enumerate(jugadores):
        if jugador1['id_usuario'] in procesados:
            continue
        
        grupo = [jugador1]
        procesados.add(jugador1['id_usuario'])
        
        for j, jugador2 in enumerate(jugadores[i+1:], i+1):
            if jugador2['id_usuario'] in procesados:
                continue
            
            # Calcular similitud del nombre completo
            sim_completo = similitud(jugador1['nombre_completo_norm'], jugador2['nombre_completo_norm'])
            
            # Calcular similitud de nombre y apellido por separado
            sim_nombre = similitud(jugador1['nombre_norm'], jugador2['nombre_norm'])
            sim_apellido = similitud(jugador1['apellido_norm'], jugador2['apellido_norm'])
            
            # Considerar similar si:
            # 1. Nombre completo es muy similar (>= 85%)
            # 2. O si nombre Y apellido son similares (ambos >= 80%)
            if (sim_completo >= UMBRAL_SIMILITUD or 
                (sim_nombre >= 0.80 and sim_apellido >= 0.80)):
                grupo.append(jugador2)
                procesados.add(jugador2['id_usuario'])
        
        if len(grupo) > 1:
            grupos_similares.append(grupo)
    
    if not grupos_similares:
        print("✅ No se encontraron jugadores duplicados o similares")
    else:
        print(f"⚠️  Se encontraron {len(grupos_similares)} grupos de jugadores similares:\n")
        
        for i, grupo in enumerate(grupos_similares, 1):
            print(f"{'=' * 80}")
            print(f"GRUPO {i}: {len(grupo)} jugadores similares")
            print(f"{'=' * 80}")
            
            for j, jugador in enumerate(grupo, 1):
                print(f"\n  Jugador {j}:")
                print(f"    ID Usuario:      {jugador['id_usuario']}")
                print(f"    Nombre:          {jugador['nombre']} {jugador['apellido']}")
                print(f"    Email:           {jugador['email']}")
                print(f"    Nombre Usuario:  {jugador['nombre_usuario']}")
                print(f"    Rating:          {jugador['rating']}")
                print(f"    Partidos:        {jugador['partidos_jugados']}")
                print(f"    Categoría:       {jugador['categoria']}")
            
            # Mostrar similitudes entre jugadores del grupo
            if len(grupo) == 2:
                sim = similitud(grupo[0]['nombre_completo_norm'], grupo[1]['nombre_completo_norm'])
                print(f"\n  📊 Similitud: {sim*100:.1f}%")
            
            # Verificar si tienen parejas
            ids = [j['id_usuario'] for j in grupo]
            
            # Construir la query con los IDs directamente
            ids_str = ','.join(str(id) for id in ids)
            query_parejas = text(f"""
                SELECT 
                    tp.id_usuario,
                    COUNT(DISTINCT tp.id) as num_parejas,
                    COUNT(DISTINCT p.id_partido) as num_partidos
                FROM (
                    SELECT id, jugador1_id as id_usuario FROM torneos_parejas
                    UNION ALL
                    SELECT id, jugador2_id as id_usuario FROM torneos_parejas
                ) tp
                LEFT JOIN partidos p ON (p.pareja1_id = tp.id OR p.pareja2_id = tp.id)
                WHERE tp.id_usuario IN ({ids_str})
                GROUP BY tp.id_usuario
            """)
            
            parejas_info = conn.execute(query_parejas).fetchall()
            
            if parejas_info:
                print(f"\n  📊 Información de parejas:")
                for info in parejas_info:
                    jugador = next(j for j in grupo if j['id_usuario'] == info.id_usuario)
                    print(f"    ID {info.id_usuario}: {info.num_parejas} parejas, {info.num_partidos} partidos")
            
            print()
        
        print(f"{'=' * 80}")
        print(f"\n📋 RESUMEN:")
        print(f"   Total de grupos similares: {len(grupos_similares)}")
        print(f"   Total de jugadores similares: {sum(len(g) for g in grupos_similares)}")
        print(f"   Umbral de similitud usado: {UMBRAL_SIMILITUD*100:.0f}%")
        
        print(f"\n💡 RECOMENDACIÓN:")
        print(f"   Para cada grupo, identifica cuál es la cuenta real (con email válido)")
        print(f"   y usa 'migrar_usuario_especifico.py' para migrar los datos del duplicado")
        print(f"   a la cuenta real.")

print("\n✅ Búsqueda completada!")
