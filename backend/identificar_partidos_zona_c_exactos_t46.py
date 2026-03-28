import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("IDENTIFICAR PARTIDOS ZONA C - NOMBRES EXACTOS")
print("=" * 80)

# Obtener todos los partidos de Zona C con nombres completos
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tp1.id as pareja1_id,
        pu1.nombre || ' ' || pu1.apellido as j1_p1,
        pu2.nombre || ' ' || pu2.apellido as j2_p1,
        tp2.id as pareja2_id,
        pu3.nombre || ' ' || pu3.apellido as j1_p2,
        pu4.nombre || ' ' || pu4.apellido as j2_p2
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46
    AND tc.nombre = '5ta'
    AND tz.nombre = 'Zona C'
    ORDER BY p.id_partido
""")

partidos = cur.fetchall()

print("\n📋 TODOS LOS PARTIDOS DE ZONA C:")
print("=" * 80)

for p in partidos:
    print(f"\nPartido {p['id_partido']}")
    if p['fecha_hora']:
        print(f"  Horario actual: {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    else:
        print(f"  Horario actual: SIN PROGRAMAR")
    print(f"  Pareja {p['pareja1_id']}: {p['j1_p1']} / {p['j2_p1']}")
    print(f"  vs")
    print(f"  Pareja {p['pareja2_id']}: {p['j1_p2']} / {p['j2_p2']}")

# Buscar jugadores específicos
print("\n" + "=" * 80)
print("BÚSQUEDA DE JUGADORES ESPECÍFICOS")
print("=" * 80)

cur.execute("""
    SELECT 
        pu.id_usuario,
        pu.nombre,
        pu.apellido,
        tp.id as pareja_id
    FROM perfil_usuarios pu
    JOIN torneos_parejas tp ON (tp.jugador1_id = pu.id_usuario OR tp.jugador2_id = pu.id_usuario)
    JOIN torneo_categorias tc ON tp.categoria_id = tc.id
    JOIN torneo_zonas tz ON tp.zona_id = tz.id
    WHERE tp.id_torneo = 46
    AND tc.nombre = '5ta'
    AND tz.nombre = 'Zona C'
    AND (
        LOWER(pu.apellido) LIKE '%paez%' OR
        LOWER(pu.apellido) LIKE '%samir%' OR
        LOWER(pu.apellido) LIKE '%gurgone%'
    )
    ORDER BY pu.apellido
""")

jugadores = cur.fetchall()

print("\n🔍 Jugadores encontrados:")
for j in jugadores:
    print(f"  {j['nombre']} {j['apellido']} (ID: {j['id_usuario']}) - Pareja {j['pareja_id']}")

# Identificar parejas
print("\n" + "=" * 80)
print("PAREJAS DE ZONA C")
print("=" * 80)

cur.execute("""
    SELECT 
        tp.id as pareja_id,
        pu1.nombre || ' ' || pu1.apellido as jugador1,
        pu2.nombre || ' ' || pu2.apellido as jugador2
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    JOIN torneo_categorias tc ON tp.categoria_id = tc.id
    JOIN torneo_zonas tz ON tp.zona_id = tz.id
    WHERE tp.id_torneo = 46
    AND tc.nombre = '5ta'
    AND tz.nombre = 'Zona C'
    ORDER BY tp.id
""")

parejas = cur.fetchall()

pareja_paez = None
pareja_samir = None
pareja_gurgone = None

for p in parejas:
    print(f"\nPareja {p['pareja_id']}: {p['jugador1']} / {p['jugador2']}")
    
    nombres_completos = f"{p['jugador1']} {p['jugador2']}".lower()
    
    if 'paez' in nombres_completos:
        pareja_paez = p['pareja_id']
        print(f"  ✅ PAREJA PAEZ identificada")
    
    if 'samir' in nombres_completos:
        pareja_samir = p['pareja_id']
        print(f"  ✅ PAREJA SAMIR identificada")
    
    if 'gurgone' in nombres_completos:
        pareja_gurgone = p['pareja_id']
        print(f"  ✅ PAREJA GURGONE identificada")

print("\n" + "=" * 80)
print("RESUMEN DE IDENTIFICACIÓN")
print("=" * 80)
print(f"Pareja Paez: {pareja_paez}")
print(f"Pareja Samir: {pareja_samir}")
print(f"Pareja Gurgone: {pareja_gurgone}")

# Identificar los 3 partidos específicos
print("\n" + "=" * 80)
print("PARTIDOS A REPROGRAMAR")
print("=" * 80)

for p in partidos:
    parejas_partido = {p['pareja1_id'], p['pareja2_id']}
    
    if pareja_paez in parejas_partido and pareja_samir in parejas_partido:
        print(f"\n✅ Partido {p['id_partido']}: PAEZ vs SAMIR")
        print(f"   Nuevo horario: Viernes 16:00")
    
    if pareja_gurgone in parejas_partido and pareja_samir in parejas_partido:
        print(f"\n✅ Partido {p['id_partido']}: GURGONE vs SAMIR")
        print(f"   Nuevo horario: Viernes 18:00")
    
    if pareja_gurgone in parejas_partido and pareja_paez in parejas_partido:
        print(f"\n✅ Partido {p['id_partido']}: GURGONE vs PAEZ")
        print(f"   Nuevo horario: Viernes 20:30")

cur.close()
conn.close()
