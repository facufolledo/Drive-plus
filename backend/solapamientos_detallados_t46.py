import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import timedelta

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("SOLAPAMIENTOS DETALLADOS - TORNEO 46")
print("=" * 80)

DURACION_PARTIDO = 70  # minutos

# Obtener todos los partidos con info completa
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
    WHERE p.id_torneo = 46
    AND p.fecha_hora IS NOT NULL
    AND p.cancha_id IS NOT NULL
    ORDER BY p.cancha_id, p.fecha_hora
""")

partidos = cur.fetchall()

# Agrupar por cancha
canchas = {}
for p in partidos:
    cancha_id = p['cancha_id']
    if cancha_id not in canchas:
        canchas[cancha_id] = []
    canchas[cancha_id].append(p)

# Detectar solapamientos
solapamientos = []

for cancha_id, partidos_cancha in canchas.items():
    partidos_cancha.sort(key=lambda x: x['fecha_hora'])
    
    for i in range(len(partidos_cancha) - 1):
        p1 = partidos_cancha[i]
        p2 = partidos_cancha[i + 1]
        
        fin_p1 = p1['fecha_hora'] + timedelta(minutes=DURACION_PARTIDO)
        tiempo_entre = (p2['fecha_hora'] - p1['fecha_hora']).total_seconds() / 60
        
        if tiempo_entre < DURACION_PARTIDO:
            solapamiento_mins = DURACION_PARTIDO - tiempo_entre
            solapamientos.append({
                'cancha_id': cancha_id,
                'partido1': p1,
                'partido2': p2,
                'solapamiento_mins': solapamiento_mins
            })

print(f"\n📊 TOTAL SOLAPAMIENTOS: {len(solapamientos)}")

if not solapamientos:
    print("\n✅ NO HAY SOLAPAMIENTOS")
else:
    for idx, s in enumerate(solapamientos, 1):
        p1 = s['partido1']
        p2 = s['partido2']
        
        print(f"\n{'=' * 80}")
        print(f"SOLAPAMIENTO #{idx} - CANCHA {s['cancha_id']}")
        print(f"{'=' * 80}")
        print(f"⏱️  Solapamiento: {s['solapamiento_mins']:.0f} minutos")
        
        print(f"\n🔴 PARTIDO {p1['id_partido']} - {p1['categoria']} {p1['zona']}")
        print(f"   📅 {p1['fecha_hora'].strftime('%A %d/%m %H:%M')} - {(p1['fecha_hora'] + timedelta(minutes=DURACION_PARTIDO)).strftime('%H:%M')}")
        print(f"   👥 Pareja {p1['pareja1_id']}: {p1['j1_p1']} / {p1['j2_p1']}")
        print(f"      vs")
        print(f"   👥 Pareja {p1['pareja2_id']}: {p1['j1_p2']} / {p1['j2_p2']}")
        
        print(f"\n🔵 PARTIDO {p2['id_partido']} - {p2['categoria']} {p2['zona']}")
        print(f"   📅 {p2['fecha_hora'].strftime('%A %d/%m %H:%M')} - {(p2['fecha_hora'] + timedelta(minutes=DURACION_PARTIDO)).strftime('%H:%M')}")
        print(f"   👥 Pareja {p2['pareja1_id']}: {p2['j1_p2']} / {p2['j2_p2']}")
        print(f"      vs")
        print(f"   👥 Pareja {p2['pareja2_id']}: {p2['j1_p2']} / {p2['j2_p2']}")

cur.close()
conn.close()
