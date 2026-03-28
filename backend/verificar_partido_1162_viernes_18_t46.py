import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR PARTIDO 1162 - VIERNES 18:00")
print("=" * 80)

# Obtener info del partido 1162
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tc.nombre as categoria,
        tz.nombre as zona,
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
    WHERE p.id_partido = 1162
""")

partido = cur.fetchone()

if not partido:
    print("\n❌ PARTIDO 1162 NO ENCONTRADO")
    cur.close()
    conn.close()
    exit()

print(f"\n📋 PARTIDO 1162 - {partido['categoria']} {partido['zona']}")
if partido['fecha_hora']:
    print(f"   Horario actual: {partido['fecha_hora'].strftime('%A %d/%m %H:%M')}")
    if partido['cancha_id']:
        print(f"   Cancha actual: {partido['cancha_id']}")
else:
    print(f"   Horario actual: SIN PROGRAMAR")

print(f"\n   Pareja {partido['pareja1_id']}: {partido['j1_p1']} / {partido['j2_p1']}")
print(f"   Pareja {partido['pareja2_id']}: {partido['j1_p2']} / {partido['j2_p2']}")

# Nuevo horario propuesto: Viernes 27/03 18:00
nuevo_horario = datetime(2026, 3, 27, 18, 0)
print(f"\n{'=' * 80}")
print(f"VERIFICAR: Viernes 27/03 18:00")
print(f"{'=' * 80}")

# 1. Verificar disponibilidad de canchas
print("\n1️⃣  DISPONIBILIDAD DE CANCHAS")
print("-" * 80)

DURACION_PARTIDO = 70

cur.execute("""
    SELECT DISTINCT cancha_id 
    FROM partidos 
    WHERE id_torneo = 46 
    AND cancha_id IS NOT NULL
    ORDER BY cancha_id
""")
canchas_torneo = [c['cancha_id'] for c in cur.fetchall()]

canchas_disponibles = []

for cancha in canchas_torneo:
    # Verificar si hay partidos que se solapen con 18:00-19:10
    cur.execute("""
        SELECT id_partido, fecha_hora
        FROM partidos
        WHERE id_torneo = 46
        AND cancha_id = %s
        AND id_partido != 1162
        AND fecha_hora >= %s
        AND fecha_hora < %s
    """, (cancha, nuevo_horario - timedelta(minutes=DURACION_PARTIDO), nuevo_horario + timedelta(minutes=DURACION_PARTIDO)))
    
    conflictos = cur.fetchall()
    
    if not conflictos:
        print(f"   ✅ Cancha {cancha}: DISPONIBLE")
        canchas_disponibles.append(cancha)
    else:
        print(f"   ❌ Cancha {cancha}: Ocupada")
        for c in conflictos:
            print(f"      - Partido {c['id_partido']}: {c['fecha_hora'].strftime('%H:%M')}")

# 2. Verificar restricciones de las parejas
print(f"\n2️⃣  RESTRICCIONES DE DISPONIBILIDAD")
print("-" * 80)

# Obtener restricciones de ambas parejas
parejas_ids = [partido['pareja1_id'], partido['pareja2_id']]

cur.execute("""
    SELECT id, disponibilidad_horaria
    FROM torneos_parejas
    WHERE id = ANY(%s)
""", (parejas_ids,))

parejas_restricciones = cur.fetchall()

todos_disponibles = True

# Viernes, horario: 18:00-19:10
for pareja in parejas_restricciones:
    pareja_id = pareja['id']
    restricciones = pareja['disponibilidad_horaria'] or []
    
    if pareja_id == partido['pareja1_id']:
        nombre_pareja = f"Pareja {pareja_id} ({partido['j1_p1']} / {partido['j2_p1']})"
    else:
        nombre_pareja = f"Pareja {pareja_id} ({partido['j1_p2']} / {partido['j2_p2']})"
    
    if not restricciones:
        print(f"   ✅ {nombre_pareja}: Sin restricciones")
        continue
    
    # Buscar restricciones del viernes
    restricciones_viernes = [r for r in restricciones if r.get('dia') == 'viernes']
    
    if not restricciones_viernes:
        print(f"   ✅ {nombre_pareja}: Sin restricciones el viernes")
        continue
    
    # Verificar si 18:00-19:10 está dentro de alguna restricción
    conflicto = False
    for r in restricciones_viernes:
        r_inicio_str = r.get('hora_inicio', '')
        r_fin_str = r.get('hora_fin', '')
        
        if not r_inicio_str or not r_fin_str:
            continue
        
        # Parsear horas (formato "HH:MM")
        r_inicio_parts = r_inicio_str.split(':')
        r_fin_parts = r_fin_str.split(':')
        
        r_inicio = int(r_inicio_parts[0]) + int(r_inicio_parts[1]) / 60
        r_fin = int(r_fin_parts[0]) + int(r_fin_parts[1]) / 60
        
        # Partido: 18:00-19:10 (18.0 - 19.17)
        partido_inicio = 18.0
        partido_fin = 19.17
        
        # Si el partido se solapa con la restricción (horario NO disponible)
        if not (partido_fin <= r_inicio or partido_inicio >= r_fin):
            conflicto = True
            print(f"   ❌ {nombre_pareja}: NO DISPONIBLE viernes {r_inicio_str}-{r_fin_str}")
            todos_disponibles = False
            break
    
    if not conflicto:
        print(f"   ✅ {nombre_pareja}: Disponible (restricciones no afectan 18:00)")

# Resumen
print(f"\n{'=' * 80}")
print("RESUMEN")
print(f"{'=' * 80}")

if canchas_disponibles and todos_disponibles:
    print(f"\n✅ SÍ SE PUEDE MOVER A VIERNES 18:00")
    print(f"\n   Canchas disponibles: {canchas_disponibles}")
    print(f"   Todas las parejas están disponibles")
elif not canchas_disponibles:
    print(f"\n❌ NO HAY CANCHAS DISPONIBLES")
elif not todos_disponibles:
    print(f"\n❌ ALGUNA PAREJA NO ESTÁ DISPONIBLE")

cur.close()
conn.close()
