import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import timedelta

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("ANÁLISIS PROBLEMA PAREJA 1037 (PALACIOS/GURGONE) - ZONA C")
print("=" * 80)

# Obtener todos los partidos de la Zona C de 5ta
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
        pu4.nombre || ' ' || pu4.apellido as j2_p2,
        tp1.disponibilidad_horaria as disp1,
        tp2.disponibilidad_horaria as disp2
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
    AND p.fecha_hora IS NOT NULL
    ORDER BY p.fecha_hora
""")

partidos_zona_c = cur.fetchall()

print(f"\n📊 PARTIDOS DE ZONA C (5ta):")
print("=" * 80)

for p in partidos_zona_c:
    print(f"\nPartido {p['id_partido']} - {p['fecha_hora'].strftime('%A %d/%m %H:%M')} - Cancha {p['cancha_id']}")
    print(f"  Pareja {p['pareja1_id']}: {p['j1_p1']} / {p['j2_p1']}")
    print(f"  vs")
    print(f"  Pareja {p['pareja2_id']}: {p['j1_p2']} / {p['j2_p2']}")
    
    # Mostrar restricciones de cada pareja
    if p['disp1']:
        restricciones_viernes = [r for r in p['disp1'] if r.get('dia') == 'viernes']
        if restricciones_viernes:
            print(f"  ⚠️  Pareja {p['pareja1_id']} restricciones viernes:")
            for r in restricciones_viernes:
                print(f"      NO disponible: {r.get('hora_inicio')}-{r.get('hora_fin')}")
    
    if p['disp2']:
        restricciones_viernes = [r for r in p['disp2'] if r.get('dia') == 'viernes']
        if restricciones_viernes:
            print(f"  ⚠️  Pareja {p['pareja2_id']} restricciones viernes:")
            for r in restricciones_viernes:
                print(f"      NO disponible: {r.get('hora_inicio')}-{r.get('hora_fin')}")

# Identificar partidos con pareja 1037
print(f"\n{'=' * 80}")
print("PARTIDOS DE PAREJA 1037 (PALACIOS/GURGONE)")
print("=" * 80)

partidos_1037 = [p for p in partidos_zona_c if p['pareja1_id'] == 1037 or p['pareja2_id'] == 1037]

for p in partidos_1037:
    rival_id = p['pareja2_id'] if p['pareja1_id'] == 1037 else p['pareja1_id']
    rival_nombre = f"{p['j1_p2']} / {p['j2_p2']}" if p['pareja1_id'] == 1037 else f"{p['j1_p1']} / {p['j2_p1']}"
    
    print(f"\n🔴 Partido {p['id_partido']}")
    print(f"   Horario: {p['fecha_hora'].strftime('%A %d/%m %H:%M')}")
    print(f"   Rival: Pareja {rival_id} ({rival_nombre})")
    
    # Verificar restricciones del rival
    rival_disp = p['disp2'] if p['pareja1_id'] == 1037 else p['disp1']
    if rival_disp:
        restricciones_viernes = [r for r in rival_disp if r.get('dia') == 'viernes']
        if restricciones_viernes:
            print(f"   ⚠️  Rival NO disponible viernes:")
            for r in restricciones_viernes:
                print(f"       {r.get('hora_inicio')}-{r.get('hora_fin')}")

# Obtener todas las parejas de Zona C
print(f"\n{'=' * 80}")
print("TODAS LAS PAREJAS DE ZONA C")
print("=" * 80)

# Obtener parejas únicas de los partidos de Zona C
parejas_ids = set()
for p in partidos_zona_c:
    parejas_ids.add(p['pareja1_id'])
    parejas_ids.add(p['pareja2_id'])

cur.execute("""
    SELECT 
        tp.id,
        pu1.nombre || ' ' || pu1.apellido as j1,
        pu2.nombre || ' ' || pu2.apellido as j2,
        tp.disponibilidad_horaria
    FROM torneos_parejas tp
    JOIN perfil_usuarios pu1 ON tp.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp.jugador2_id = pu2.id_usuario
    WHERE tp.id = ANY(%s)
    ORDER BY tp.id
""", (list(parejas_ids),))

parejas_zona_c = cur.fetchall()

for pareja in parejas_zona_c:
    print(f"\nPareja {pareja['id']}: {pareja['j1']} / {pareja['j2']}")
    
    if pareja['disponibilidad_horaria']:
        restricciones_viernes = [r for r in pareja['disponibilidad_horaria'] if r.get('dia') == 'viernes']
        if restricciones_viernes:
            print(f"  ⚠️  NO disponible viernes:")
            for r in restricciones_viernes:
                print(f"      {r.get('hora_inicio')}-{r.get('hora_fin')}")
        else:
            print(f"  ✅ Disponible todo el viernes")
    else:
        print(f"  ✅ Sin restricciones")

print(f"\n{'=' * 80}")
print("ANÁLISIS Y RECOMENDACIONES")
print("=" * 80)

print("""
PROBLEMA:
- Pareja 1037 (Palacios/Gurgone) tiene partidos a las 18:00 y 20:00
- Sus rivales tienen restricciones después de las 19:00 o 20:00

SOLUCIÓN POSIBLE:
Intercambiar pareja 1037 con otra pareja de una zona diferente que:
1. Tenga disponibilidad compatible con los horarios 18:00 y 20:00
2. Sus rivales actuales puedan jugar en los horarios de la Zona C

ZONAS A CONSIDERAR PARA INTERCAMBIO:
- Buscar parejas en otras zonas (A, B, D, E) que tengan mejor disponibilidad
""")

cur.close()
conn.close()
