import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import json

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CREAR E INSCRIBIR PRINCIPIANTE - TORNEO 46")
print("=" * 80)

# Mapeo manual basado en la búsqueda confirmada por el usuario
jugadores_existentes = {
    'Jere Vera': 228,
    'Damian Agostini': 173,
    'Dario Barrionuevo': 175
}

# Parejas con sus datos completos
parejas_data = [
    {
        'jugador1': {'nombre': 'Benjamín', 'apellido': 'Jatuff'},
        'jugador2': {'nombre': 'Manuel', 'apellido': 'Alcazar'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '16:59'},
            {'dias': ['viernes'], 'horaInicio': '17:01', 'horaFin': '23:59'}
        ]
    },
    {
        'jugador1': {'nombre': 'Camilo', 'apellido': 'Ríos'},
        'jugador2': {'nombre': 'Agusto', 'apellido': 'Aballay'},
        'restricciones': []
    },
    {
        'jugador1': {'nombre': 'Nicolas', 'apellido': 'Velázquez'},
        'jugador2': {'nombre': 'Francisco', 'apellido': 'Zurita'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '16:59'}
        ]
    },
    {
        'jugador1': {'nombre': 'Leonel', 'apellido': 'Córdoba'},
        'jugador2': {'nombre': 'Kevin', 'apellido': 'Paez'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '20:59'}
        ]
    },
    {
        'jugador1': {'nombre': 'Jesús', 'apellido': 'Sotomayor'},
        'jugador2': {'nombre': 'Mateo', 'apellido': 'Diaz'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '19:29'}
        ]
    },
    {
        'jugador1': {'nombre': 'Imanol', 'apellido': 'Morales'},
        'jugador2': {'nombre': 'Carlos', 'apellido': 'Vera'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '18:59'}
        ]
    },
    {
        'jugador1': {'nombre': 'Jere', 'apellido': 'Vera'},
        'jugador2': {'nombre': 'Ariel', 'apellido': 'Calderón'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '17:59'},
            {'dias': ['sábado'], 'horaInicio': '00:00', 'horaFin': '10:59'}
        ]
    },
    {
        'jugador1': {'nombre': 'Facundo', 'apellido': 'Ludueña'},
        'jugador2': {'nombre': 'Stefano', 'apellido': 'Apostolo'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '14:00', 'horaFin': '16:59'},
            {'dias': ['viernes'], 'horaInicio': '22:00', 'horaFin': '23:59'}
        ]
    },
    {
        'jugador1': {'nombre': 'Damian', 'apellido': 'Agostini'},
        'jugador2': {'nombre': 'Benjamin', 'apellido': 'Paez'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '23:59'},
            {'dias': ['sábado'], 'horaInicio': '00:00', 'horaFin': '09:59'}
        ]
    },
    {
        'jugador1': {'nombre': 'Tobias', 'apellido': 'Villalba'},
        'jugador2': {'nombre': 'Mariano', 'apellido': 'Alvarado'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '19:00', 'horaFin': '23:59'}
        ]
    },
    {
        'jugador1': {'nombre': 'Pablo', 'apellido': 'Toledo'},
        'jugador2': {'nombre': 'Dario', 'apellido': 'Barrionuevo'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '16:59'}
        ]
    },
    {
        'jugador1': {'nombre': 'Santino', 'apellido': 'Molina'},
        'jugador2': {'nombre': 'Ramiro', 'apellido': 'Dávila'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '23:59'},
            {'dias': ['sábado'], 'horaInicio': '00:00', 'horaFin': '13:59'}
        ]
    }
]

# Obtener categoría Principiante
cur.execute("""
    SELECT id FROM torneo_categorias
    WHERE torneo_id = 46 AND nombre = 'Principiante'
""")

categoria = cur.fetchone()
if not categoria:
    print("❌ Categoría Principiante no encontrada")
    cur.close()
    conn.close()
    exit(1)

categoria_id = categoria['id']
print(f"✅ Categoría Principiante ID: {categoria_id}")

def obtener_o_crear_jugador(nombre, apellido):
    """Obtiene ID de jugador existente o crea uno nuevo"""
    
    # Buscar en jugadores existentes mapeados
    key = f"{nombre} {apellido}"
    if key in jugadores_existentes:
        print(f"  ✅ Existente: {nombre} {apellido} (ID: {jugadores_existentes[key]})")
        return jugadores_existentes[key]
    
    # Buscar en BD
    cur.execute("""
        SELECT id_usuario
        FROM perfil_usuarios
        WHERE LOWER(nombre) = LOWER(%s) AND LOWER(apellido) = LOWER(%s)
    """, (nombre, apellido))
    
    jugador = cur.fetchone()
    if jugador:
        print(f"  ✅ Encontrado: {nombre} {apellido} (ID: {jugador['id_usuario']})")
        return jugador['id_usuario']
    
    # Crear nuevo jugador (primero en usuarios, luego en perfil_usuarios)
    # Generar email y nombre_usuario temporal
    nombre_usuario_temp = f"{nombre.lower()}{apellido.lower()}"
    email_temp = f"{nombre.lower()}.{apellido.lower()}@temp.com"
    
    # Insertar en usuarios
    cur.execute("""
        INSERT INTO usuarios (nombre_usuario, email, password_hash)
        VALUES (%s, %s, 'temp_hash')
        RETURNING id_usuario
    """, (nombre_usuario_temp, email_temp))
    
    nuevo_id = cur.fetchone()['id_usuario']
    
    # Insertar en perfil_usuarios
    cur.execute("""
        INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
        VALUES (%s, %s, %s)
    """, (nuevo_id, nombre, apellido))
    
    print(f"  ✨ CREADO: {nombre} {apellido} (ID: {nuevo_id})")
    return nuevo_id

# Procesar parejas
print("\n" + "=" * 80)
print("PROCESANDO PAREJAS")
print("=" * 80)

try:
    parejas_inscritas = []
    
    for idx, pareja in enumerate(parejas_data, 1):
        print(f"\n{idx}. {pareja['jugador1']['nombre']} {pareja['jugador1']['apellido']} / {pareja['jugador2']['nombre']} {pareja['jugador2']['apellido']}")
        
        j1_id = obtener_o_crear_jugador(pareja['jugador1']['nombre'], pareja['jugador1']['apellido'])
        j2_id = obtener_o_crear_jugador(pareja['jugador2']['nombre'], pareja['jugador2']['apellido'])
        
        # Inscribir pareja
        cur.execute("""
            INSERT INTO torneos_parejas (
                torneo_id, jugador1_id, jugador2_id, categoria_id, disponibilidad_horaria
            )
            VALUES (46, %s, %s, %s, %s::jsonb)
            RETURNING id
        """, (
            j1_id,
            j2_id,
            categoria_id,
            json.dumps(pareja['restricciones']) if pareja['restricciones'] else None
        ))
        
        pareja_id = cur.fetchone()['id']
        parejas_inscritas.append(pareja_id)
        
        print(f"  ✅ Pareja inscrita (ID: {pareja_id})")
        if pareja['restricciones']:
            for r in pareja['restricciones']:
                dias = ', '.join(r['dias'])
                print(f"     - NO disponible {dias} de {r['horaInicio']} a {r['horaFin']}")
    
    conn.commit()
    
    print("\n" + "=" * 80)
    print(f"✅ {len(parejas_inscritas)} PAREJAS INSCRITAS EXITOSAMENTE")
    print("=" * 80)
    print(f"\nIDs de parejas: {', '.join(map(str, parejas_inscritas))}")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
