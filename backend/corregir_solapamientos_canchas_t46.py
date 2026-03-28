import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("CORREGIR SOLAPAMIENTOS DE CANCHAS - TORNEO 46")
print("=" * 80)

# SOLAPAMIENTO #1: Mover Partido 1252 de Cancha 92 a Cancha 93
print("\n1️⃣  SOLAPAMIENTO #1 - Viernes 27/03 17:20")
print("=" * 80)

cur.execute("SELECT * FROM partidos WHERE id_partido = 1252")
partido1 = cur.fetchone()

print(f"Partido 1252 (Principiante Zona B)")
print(f"  Cancha actual: {partido1['cancha_id']}")
print(f"  Horario: {partido1['fecha_hora'].strftime('%A %d/%m %H:%M')}")
print(f"\n  ➡️  Moviendo a Cancha 93...")

cur.execute("""
    UPDATE partidos 
    SET cancha_id = 93
    WHERE id_partido = 1252
""")

print(f"  ✅ Partido 1252 movido a Cancha 93")

# SOLAPAMIENTO #2: Mover Partido 1166 de Cancha 92 a Cancha 94
print("\n2️⃣  SOLAPAMIENTO #2 - Sábado 28/03 12:30")
print("=" * 80)

cur.execute("SELECT * FROM partidos WHERE id_partido = 1166")
partido2 = cur.fetchone()

print(f"Partido 1166 (5ta Zona D)")
print(f"  Cancha actual: {partido2['cancha_id']}")
print(f"  Horario: {partido2['fecha_hora'].strftime('%A %d/%m %H:%M')}")
print(f"\n  ➡️  Moviendo a Cancha 94...")

cur.execute("""
    UPDATE partidos 
    SET cancha_id = 94
    WHERE id_partido = 1166
""")

print(f"  ✅ Partido 1166 movido a Cancha 94")

# Commit
conn.commit()

print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL")
print("=" * 80)

# Verificar que no haya más solapamientos críticos
from datetime import timedelta

DURACION_PARTIDO = 70

cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        p.cancha_id,
        tc.nombre as categoria,
        tz.nombre as zona
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
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
        
        tiempo_entre = (p2['fecha_hora'] - p1['fecha_hora']).total_seconds() / 60
        
        if tiempo_entre < DURACION_PARTIDO:
            solapamiento_mins = DURACION_PARTIDO - tiempo_entre
            solapamientos.append({
                'cancha_id': cancha_id,
                'partido1': p1['id_partido'],
                'partido2': p2['id_partido'],
                'solapamiento_mins': solapamiento_mins
            })

print(f"\n📊 Solapamientos restantes: {len(solapamientos)}")

if solapamientos:
    for s in solapamientos:
        print(f"\n⚠️  Cancha {s['cancha_id']}: Partidos {s['partido1']} y {s['partido2']}")
        print(f"   Solapamiento: {s['solapamiento_mins']:.0f} minutos")
        if s['solapamiento_mins'] <= 10:
            print(f"   ✅ Aceptable (≤10 minutos)")
else:
    print("\n✅ NO HAY SOLAPAMIENTOS")

print("\n" + "=" * 80)
print("✅ CORRECCIÓN COMPLETADA")
print("=" * 80)

cur.close()
conn.close()
