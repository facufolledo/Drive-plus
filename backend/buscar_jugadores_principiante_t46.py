import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("BÚSQUEDA EXHAUSTIVA DE JUGADORES PRINCIPIANTE")
print("=" * 80)

# Lista de jugadores a buscar
jugadores_buscar = [
    ('Benjamín', 'Jatuff'),
    ('Manuel', 'Alcazar'),
    ('Camilo', 'Ríos'),
    ('Agusto', 'Aballay'),
    ('Nicolas', 'Velázquez'),
    ('Francisco', 'Zurita'),
    ('Leonel', 'Córdoba'),
    ('Kevin', 'Paez'),
    ('Jesús', 'Sotomayor'),
    ('Mateo', 'Diaz'),
    ('Imanol', 'Morales'),
    ('Carlos', 'Vera'),
    ('Jere', 'Vera'),
    ('Ariel', 'Calderón'),
    ('Facundo', 'Ludueña'),
    ('Stefano', 'Apostolo'),
    ('Damián', 'Agostini'),
    ('Benjamin', 'Paez'),
    ('Tobias', 'Villalba'),
    ('Mariano', 'Alvarado'),
    ('Pablo', 'Toledo'),
    ('Darío', 'Barrionuevo'),
    ('Ramiro', 'Dávila')
]

def buscar_jugador_flexible(nombre, apellido):
    """Busca un jugador con múltiples variaciones"""
    
    # 1. Búsqueda exacta
    cur.execute("""
        SELECT id_usuario, nombre, apellido
        FROM perfil_usuarios
        WHERE LOWER(nombre) = LOWER(%s) AND LOWER(apellido) = LOWER(%s)
    """, (nombre, apellido))
    
    resultado = cur.fetchone()
    if resultado:
        return resultado, 'exacta'
    
    # 2. Búsqueda invertida (apellido como nombre y viceversa)
    cur.execute("""
        SELECT id_usuario, nombre, apellido
        FROM perfil_usuarios
        WHERE LOWER(nombre) = LOWER(%s) AND LOWER(apellido) = LOWER(%s)
    """, (apellido, nombre))
    
    resultado = cur.fetchone()
    if resultado:
        return resultado, 'invertida'
    
    # 3. Búsqueda por similitud en nombre
    cur.execute("""
        SELECT id_usuario, nombre, apellido
        FROM perfil_usuarios
        WHERE LOWER(nombre) LIKE LOWER(%s) AND LOWER(apellido) LIKE LOWER(%s)
    """, (f'%{nombre}%', f'%{apellido}%'))
    
    resultado = cur.fetchone()
    if resultado:
        return resultado, 'similar'
    
    # 4. Búsqueda por similitud invertida
    cur.execute("""
        SELECT id_usuario, nombre, apellido
        FROM perfil_usuarios
        WHERE LOWER(nombre) LIKE LOWER(%s) AND LOWER(apellido) LIKE LOWER(%s)
    """, (f'%{apellido}%', f'%{nombre}%'))
    
    resultado = cur.fetchone()
    if resultado:
        return resultado, 'similar_invertida'
    
    # 5. Búsqueda solo por apellido (más flexible)
    cur.execute("""
        SELECT id_usuario, nombre, apellido
        FROM perfil_usuarios
        WHERE LOWER(apellido) LIKE LOWER(%s)
        ORDER BY id_usuario DESC
        LIMIT 5
    """, (f'%{apellido}%',))
    
    resultados = cur.fetchall()
    if resultados:
        return resultados, 'por_apellido'
    
    return None, None

# Buscar cada jugador
encontrados = []
no_encontrados = []

for nombre, apellido in jugadores_buscar:
    print(f"\n🔍 Buscando: {nombre} {apellido}")
    
    resultado, tipo = buscar_jugador_flexible(nombre, apellido)
    
    if resultado:
        if tipo == 'por_apellido':
            print(f"  ⚠️  Múltiples coincidencias por apellido:")
            for r in resultado:
                print(f"     - {r['nombre']} {r['apellido']} (ID: {r['id_usuario']})")
            no_encontrados.append((nombre, apellido))
        else:
            print(f"  ✅ Encontrado ({tipo}): {resultado['nombre']} {resultado['apellido']} (ID: {resultado['id_usuario']})")
            encontrados.append({
                'buscado': f"{nombre} {apellido}",
                'encontrado': f"{resultado['nombre']} {resultado['apellido']}",
                'id': resultado['id_usuario'],
                'tipo': tipo
            })
    else:
        print(f"  ❌ NO encontrado")
        no_encontrados.append((nombre, apellido))

print("\n" + "=" * 80)
print(f"RESUMEN: {len(encontrados)} encontrados, {len(no_encontrados)} no encontrados")
print("=" * 80)

if encontrados:
    print("\n✅ JUGADORES ENCONTRADOS:")
    for j in encontrados:
        print(f"  {j['buscado']} → {j['encontrado']} (ID: {j['id']}) [{j['tipo']}]")

if no_encontrados:
    print("\n❌ JUGADORES NO ENCONTRADOS:")
    for nombre, apellido in no_encontrados:
        print(f"  - {nombre} {apellido}")

cur.close()
conn.close()
