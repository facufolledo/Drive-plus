import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("INSCRIPCIÓN PRINCIPIANTE - TORNEO 46")
print("=" * 80)

# Datos de las parejas
parejas_data = [
    {
        'jugador1': {'nombre': 'Benjamín', 'apellido': 'Jatuff'},
        'jugador2': {'nombre': 'Manuel', 'apellido': 'Alcazar'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '16:59'},
            {'dias': ['viernes'], 'horaInicio': '17:01', 'horaFin': '23:59'}
        ]  # Solo viernes 17:00, sábado libre
    },
    {
        'jugador1': {'nombre': 'Camilo', 'apellido': 'Ríos'},
        'jugador2': {'nombre': 'Agusto', 'apellido': 'Aballay'},
        'restricciones': []  # Libre
    },
    {
        'jugador1': {'nombre': 'Nicolas', 'apellido': 'Velázquez'},
        'jugador2': {'nombre': 'Francisco', 'apellido': 'Zurita'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '16:59'}
        ]  # Viernes después de 17:00
    },
    {
        'jugador1': {'nombre': 'Leonel', 'apellido': 'Córdoba'},
        'jugador2': {'nombre': 'Kevin', 'apellido': 'Paez'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '20:59'}
        ]  # Viernes después de 21:00
    },
    {
        'jugador1': {'nombre': 'Jesús', 'apellido': 'Sotomayor'},
        'jugador2': {'nombre': 'Mateo', 'apellido': 'Diaz'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '19:29'}
        ]  # Viernes después de 19:30
    },
    {
        'jugador1': {'nombre': 'Imanol', 'apellido': 'Morales'},
        'jugador2': {'nombre': 'Carlos', 'apellido': 'Vera'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '18:59'}
        ]  # Viernes después de 19:00
    },
    {
        'jugador1': {'nombre': 'Jere', 'apellido': 'Vera'},
        'jugador2': {'nombre': 'Ariel', 'apellido': 'Calderón'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '17:59'},
            {'dias': ['sábado'], 'horaInicio': '00:00', 'horaFin': '10:59'}
        ]  # Viernes después de 18:00, sábado después de 11:00
    },
    {
        'jugador1': {'nombre': 'Facundo', 'apellido': 'Ludueña'},
        'jugador2': {'nombre': 'Stefano', 'apellido': 'Apostolo'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '14:00', 'horaFin': '16:59'},
            {'dias': ['viernes'], 'horaInicio': '22:00', 'horaFin': '23:59'}
        ]  # Viernes +14 -17 +22 (disponible 14-17 y después de 22)
        # NOTA: Debe jugar con Agusto Aballay y Camilo Ríos
    },
    {
        'jugador1': {'nombre': 'Damián', 'apellido': 'Agostini'},
        'jugador2': {'nombre': 'Benjamin', 'apellido': 'Paez'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '23:59'},
            {'dias': ['sábado'], 'horaInicio': '00:00', 'horaFin': '09:59'}
        ]  # Viernes no puede, sábado después de 10:00
    },
    {
        'jugador1': {'nombre': 'Tobias', 'apellido': 'Villalba'},
        'jugador2': {'nombre': 'Mariano', 'apellido': 'Alvarado'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '19:00', 'horaFin': '23:59'}
        ]  # Viernes antes de 19:00
    },
    {
        'jugador1': {'nombre': 'Pablo', 'apellido': 'Toledo'},
        'jugador2': {'nombre': 'Darío', 'apellido': 'Barrionuevo'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '16:59'}
        ]  # Viernes después de 17:00
    },
    {
        'jugador1': {'nombre': 'Santino', 'apellido': 'Molina'},
        'jugador2': {'nombre': 'Ramiro', 'apellido': 'Dávila'},
        'restricciones': [
            {'dias': ['viernes'], 'horaInicio': '00:00', 'horaFin': '23:59'},
            {'dias': ['sábado'], 'horaInicio': '00:00', 'horaFin': '13:59'}
        ]  # Viernes no puede, sábado después de 14:00
    }
]

# Obtener ID de categoría Principiante
cur.execute("""
    SELECT id, nombre
    FROM torneo_categorias
    WHERE torneo_id = 46 AND nombre = 'Principiante'
""")

categoria = cur.fetchone()

if not categoria:
    print("❌ Categoría Principiante no encontrada en torneo 46")
    print("\n📋 Categorías disponibles:")
    cur.execute("""
        SELECT id, nombre
        FROM torneo_categorias
        WHERE torneo_id = 46
        ORDER BY nombre
    """)
    for cat in cur.fetchall():
        print(f"  - {cat['nombre']} (ID: {cat['id']})")
    
    cur.close()
    conn.close()
    exit(1)

print(f"\n✅ Categoría encontrada: {categoria['nombre']} (ID: {categoria['id']})")

# Función para buscar o crear jugador
def buscar_o_crear_jugador(nombre, apellido):
    # Buscar jugador existente
    cur.execute("""
        SELECT id_usuario, nombre, apellido
        FROM perfil_usuarios
        WHERE LOWER(nombre) = LOWER(%s) AND LOWER(apellido) = LOWER(%s)
    """, (nombre, apellido))
    
    jugador = cur.fetchone()
    
    if jugador:
        print(f"  ✅ Encontrado: {jugador['nombre']} {jugador['apellido']} (ID: {jugador['id_usuario']})")
        return jugador['id_usuario']
    else:
        print(f"  ⚠️  No encontrado: {nombre} {apellido} - necesita ser creado en el sistema")
        return None

# Procesar cada pareja
print(f"\n" + "=" * 80)
print("BUSCANDO JUGADORES")
print("=" * 80)

parejas_procesadas = []
jugadores_faltantes = []

for idx, pareja in enumerate(parejas_data, 1):
    print(f"\n{idx}. Pareja: {pareja['jugador1']['nombre']} {pareja['jugador1']['apellido']} / {pareja['jugador2']['nombre']} {pareja['jugador2']['apellido']}")
    
    j1_id = buscar_o_crear_jugador(pareja['jugador1']['nombre'], pareja['jugador1']['apellido'])
    j2_id = buscar_o_crear_jugador(pareja['jugador2']['nombre'], pareja['jugador2']['apellido'])
    
    if j1_id and j2_id:
        parejas_procesadas.append({
            'jugador1_id': j1_id,
            'jugador2_id': j2_id,
            'restricciones': pareja['restricciones'],
            'nombres': f"{pareja['jugador1']['nombre']} {pareja['jugador1']['apellido']} / {pareja['jugador2']['nombre']} {pareja['jugador2']['apellido']}"
        })
    else:
        if not j1_id:
            jugadores_faltantes.append(f"{pareja['jugador1']['nombre']} {pareja['jugador1']['apellido']}")
        if not j2_id:
            jugadores_faltantes.append(f"{pareja['jugador2']['nombre']} {pareja['jugador2']['apellido']}")

if jugadores_faltantes:
    print(f"\n" + "=" * 80)
    print(f"⚠️  JUGADORES FALTANTES ({len(jugadores_faltantes)}):")
    print("=" * 80)
    for j in jugadores_faltantes:
        print(f"  - {j}")
    print("\nEstos jugadores deben ser creados primero en el sistema.")
    
    respuesta = input("\n¿Continuar con las parejas que tienen ambos jugadores? (s/n): ")
    if respuesta.lower() != 's':
        print("\n❌ Inscripción cancelada")
        cur.close()
        conn.close()
        exit(0)

if not parejas_procesadas:
    print("\n❌ No hay parejas completas para inscribir")
    cur.close()
    conn.close()
    exit(1)

# Inscribir parejas
print(f"\n" + "=" * 80)
print(f"INSCRIBIENDO {len(parejas_procesadas)} PAREJAS")
print("=" * 80)

try:
    for idx, pareja in enumerate(parejas_procesadas, 1):
        # Insertar pareja
        cur.execute("""
            INSERT INTO torneos_parejas (
                jugador1_id, jugador2_id, categoria_id, disponibilidad_horaria
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            pareja['jugador1_id'],
            pareja['jugador2_id'],
            categoria['id'],
            pareja['restricciones'] if pareja['restricciones'] else None
        ))
        
        pareja_id = cur.fetchone()['id']
        
        print(f"\n{idx}. ✅ Pareja {pareja_id}: {pareja['nombres']}")
        if pareja['restricciones']:
            print(f"   Restricciones:")
            for r in pareja['restricciones']:
                dias = ', '.join(r['dias'])
                print(f"     - NO disponible {dias} de {r['horaInicio']} a {r['horaFin']}")
        else:
            print(f"   Sin restricciones")
    
    conn.commit()
    
    print(f"\n" + "=" * 80)
    print(f"✅ {len(parejas_procesadas)} PAREJAS INSCRITAS EXITOSAMENTE")
    print("=" * 80)
    
    if jugadores_faltantes:
        print(f"\n⚠️  Nota: {len(jugadores_faltantes)} jugadores no pudieron ser inscritos (no existen en el sistema)")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
