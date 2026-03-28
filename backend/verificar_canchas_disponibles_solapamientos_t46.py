import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("VERIFICAR CANCHAS DISPONIBLES PARA RESOLVER SOLAPAMIENTOS - TORNEO 46")
print("=" * 80)

DURACION_PARTIDO = 70  # minutos

# Obtener todas las canchas del torneo
cur.execute("""
    SELECT DISTINCT cancha_id 
    FROM partidos 
    WHERE id_torneo = 46 
    AND cancha_id IS NOT NULL
    ORDER BY cancha_id
""")
canchas_torneo = [c['cancha_id'] for c in cur.fetchall()]
print(f"\n🏟️  Canchas del torneo: {canchas_torneo}")

# SOLAPAMIENTO #1: Viernes 27/03 17:00-18:30 en Cancha 92
print(f"\n{'=' * 80}")
print("SOLAPAMIENTO #1 - Viernes 27/03 17:00-18:30 (Cancha 92)")
print(f"{'=' * 80}")
print("Partido 1163 (5ta Zona C): 17:00-18:10")
print("Partido 1252 (Principiante Zona B): 17:20-18:30")

horario1_inicio = datetime(2026, 3, 27, 17, 0)
horario1_fin = datetime(2026, 3, 27, 18, 30)

for cancha in canchas_torneo:
    if cancha == 92:
        continue
    
    # Verificar si la cancha está libre en ese rango
    cur.execute("""
        SELECT id_partido, fecha_hora
        FROM partidos
        WHERE id_torneo = 46
        AND cancha_id = %s
        AND fecha_hora >= %s
        AND fecha_hora < %s
    """, (cancha, horario1_inicio - timedelta(minutes=70), horario1_fin))
    
    partidos_conflicto = cur.fetchall()
    
    if not partidos_conflicto:
        print(f"\n✅ Cancha {cancha}: DISPONIBLE todo el rango 17:00-18:30")
    else:
        print(f"\n❌ Cancha {cancha}: Ocupada")
        for p in partidos_conflicto:
            print(f"   - Partido {p['id_partido']}: {p['fecha_hora'].strftime('%H:%M')}")

# SOLAPAMIENTO #2: Sábado 28/03 11:30-13:40 en Cancha 92
print(f"\n{'=' * 80}")
print("SOLAPAMIENTO #2 - Sábado 28/03 11:30-13:40 (Cancha 92)")
print(f"{'=' * 80}")
print("Partido 1164 (5ta Zona C): 11:30-12:40")
print("Partido 1166 (5ta Zona D): 12:30-13:40")

horario2_inicio = datetime(2026, 3, 28, 11, 30)
horario2_fin = datetime(2026, 3, 28, 13, 40)

for cancha in canchas_torneo:
    if cancha == 92:
        continue
    
    cur.execute("""
        SELECT id_partido, fecha_hora
        FROM partidos
        WHERE id_torneo = 46
        AND cancha_id = %s
        AND fecha_hora >= %s
        AND fecha_hora < %s
    """, (cancha, horario2_inicio - timedelta(minutes=70), horario2_fin))
    
    partidos_conflicto = cur.fetchall()
    
    if not partidos_conflicto:
        print(f"\n✅ Cancha {cancha}: DISPONIBLE todo el rango 11:30-13:40")
    else:
        print(f"\n❌ Cancha {cancha}: Ocupada")
        for p in partidos_conflicto:
            print(f"   - Partido {p['id_partido']}: {p['fecha_hora'].strftime('%H:%M')}")

# SOLAPAMIENTO #3: Sábado 28/03 15:00-17:10 en Cancha 93
print(f"\n{'=' * 80}")
print("SOLAPAMIENTO #3 - Sábado 28/03 15:00-17:10 (Cancha 93)")
print(f"{'=' * 80}")
print("Partido 1168 (5ta Zona E): 15:00-16:10")
print("Partido 1160 (5ta Zona B): 16:00-17:10")

horario3_inicio = datetime(2026, 3, 28, 15, 0)
horario3_fin = datetime(2026, 3, 28, 17, 10)

for cancha in canchas_torneo:
    if cancha == 93:
        continue
    
    cur.execute("""
        SELECT id_partido, fecha_hora
        FROM partidos
        WHERE id_torneo = 46
        AND cancha_id = %s
        AND fecha_hora >= %s
        AND fecha_hora < %s
    """, (cancha, horario3_inicio - timedelta(minutes=70), horario3_fin))
    
    partidos_conflicto = cur.fetchall()
    
    if not partidos_conflicto:
        print(f"\n✅ Cancha {cancha}: DISPONIBLE todo el rango 15:00-17:10")
    else:
        print(f"\n❌ Cancha {cancha}: Ocupada")
        for p in partidos_conflicto:
            print(f"   - Partido {p['id_partido']}: {p['fecha_hora'].strftime('%H:%M')}")

cur.close()
conn.close()
