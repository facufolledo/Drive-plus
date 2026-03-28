import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import timedelta

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR SOLAPAMIENTOS DE CANCHAS - TORNEO 46")
print("=" * 80)

DURACION_PARTIDO = 70  # minutos

# Obtener todos los partidos programados del torneo 46
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tc.nombre as categoria,
        tz.nombre as zona,
        tp1.id as pareja1_id,
        tp2.id as pareja2_id
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
    LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    WHERE p.id_torneo = 46
    AND p.fecha_hora IS NOT NULL
    AND p.cancha_id IS NOT NULL
    ORDER BY p.cancha_id, p.fecha_hora
""")

partidos = cur.fetchall()

print(f"\n📊 PARTIDOS PROGRAMADOS: {len(partidos)}")

# Agrupar por cancha
canchas = {}
for p in partidos:
    cancha_id = p['cancha_id']
    if cancha_id not in canchas:
        canchas[cancha_id] = []
    canchas[cancha_id].append(p)

print(f"🏟️  CANCHAS UTILIZADAS: {len(canchas)}")

# Verificar solapamientos por cancha
solapamientos = []

for cancha_id, partidos_cancha in canchas.items():
    print(f"\n{'=' * 80}")
    print(f"CANCHA {cancha_id} - {len(partidos_cancha)} partidos")
    print(f"{'=' * 80}")
    
    # Ordenar por fecha_hora
    partidos_cancha.sort(key=lambda x: x['fecha_hora'])
    
    for i, p in enumerate(partidos_cancha):
        fecha_hora = p['fecha_hora'].strftime('%a %d/%m %H:%M')
        fin_partido = p['fecha_hora'] + timedelta(minutes=DURACION_PARTIDO)
        
        print(f"\n{i+1}. Partido {p['id_partido']} - {p['categoria']} {p['zona']}")
        print(f"   {fecha_hora} - {fin_partido.strftime('%H:%M')}")
        print(f"   P{p['pareja1_id']} vs P{p['pareja2_id']}")
        
        # Verificar solapamiento con el siguiente partido
        if i < len(partidos_cancha) - 1:
            siguiente = partidos_cancha[i + 1]
            tiempo_entre_partidos = (siguiente['fecha_hora'] - p['fecha_hora']).total_seconds() / 60
            
            if tiempo_entre_partidos < DURACION_PARTIDO:
                solapamiento_mins = DURACION_PARTIDO - tiempo_entre_partidos
                print(f"   ⚠️  SOLAPAMIENTO: {solapamiento_mins:.0f} minutos con partido {siguiente['id_partido']}")
                
                solapamientos.append({
                    'cancha_id': cancha_id,
                    'partido1': p['id_partido'],
                    'partido2': siguiente['id_partido'],
                    'categoria1': p['categoria'],
                    'categoria2': siguiente['categoria'],
                    'solapamiento_mins': solapamiento_mins,
                    'horario1': p['fecha_hora'].strftime('%a %d/%m %H:%M'),
                    'horario2': siguiente['fecha_hora'].strftime('%a %d/%m %H:%M')
                })
            else:
                print(f"   ✅ {tiempo_entre_partidos:.0f} minutos hasta siguiente partido")

# Resumen de solapamientos
print(f"\n{'=' * 80}")
print("RESUMEN DE SOLAPAMIENTOS")
print(f"{'=' * 80}")

if not solapamientos:
    print("\n✅ NO HAY SOLAPAMIENTOS DE CANCHAS")
else:
    print(f"\n⚠️  {len(solapamientos)} SOLAPAMIENTOS DETECTADOS:")
    
    for s in solapamientos:
        print(f"\n❌ Cancha {s['cancha_id']}")
        print(f"   Partido {s['partido1']} ({s['categoria1']}) - {s['horario1']}")
        print(f"   Partido {s['partido2']} ({s['categoria2']}) - {s['horario2']}")
        print(f"   Solapamiento: {s['solapamiento_mins']:.0f} minutos")

# Estadísticas por categoría
print(f"\n{'=' * 80}")
print("ESTADÍSTICAS POR CATEGORÍA")
print(f"{'=' * 80}")

cur.execute("""
    SELECT 
        tc.nombre as categoria,
        COUNT(p.id_partido) as total_partidos,
        COUNT(DISTINCT p.cancha_id) as canchas_usadas,
        MIN(p.fecha_hora) as primer_partido,
        MAX(p.fecha_hora) as ultimo_partido
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    WHERE p.id_torneo = 46
    AND p.fecha_hora IS NOT NULL
    GROUP BY tc.nombre
    ORDER BY tc.nombre
""")

stats = cur.fetchall()

for s in stats:
    print(f"\n{s['categoria']}")
    print(f"  - Partidos: {s['total_partidos']}")
    print(f"  - Canchas usadas: {s['canchas_usadas']}")
    if s['primer_partido'] and s['ultimo_partido']:
        print(f"  - Primer partido: {s['primer_partido'].strftime('%a %d/%m %H:%M')}")
        print(f"  - Último partido: {s['ultimo_partido'].strftime('%a %d/%m %H:%M')}")

cur.close()
conn.close()
