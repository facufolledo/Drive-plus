"""Verificar que todos los partidos de 7ma esten correctamente programados"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

def conectar_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url.startswith('postgresql+pg8000://'):
        db_url = db_url.replace('postgresql+pg8000://', 'postgresql://')
    return psycopg2.connect(db_url)

conn = conectar_db()
cur = conn.cursor(cursor_factory=RealDictCursor)

# Listar todos los partidos de 7ma ordenados por fecha
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        z.nombre as zona_nombre,
        pu1.nombre || ' ' || pu1.apellido || ' / ' || pu2.nombre || ' ' || pu2.apellido as pareja1_nombre,
        pu3.nombre || ' ' || pu3.apellido || ' / ' || pu4.nombre || ' ' || pu4.apellido as pareja2_nombre
    FROM partidos p
    LEFT JOIN torneo_zonas z ON p.zona_id = z.id
    LEFT JOIN torneos_parejas pa1 ON p.pareja1_id = pa1.id
    LEFT JOIN perfil_usuarios pu1 ON pa1.jugador1_id = pu1.id_usuario
    LEFT JOIN perfil_usuarios pu2 ON pa1.jugador2_id = pu2.id_usuario
    LEFT JOIN torneos_parejas pa2 ON p.pareja2_id = pa2.id
    LEFT JOIN perfil_usuarios pu3 ON pa2.jugador1_id = pu3.id_usuario
    LEFT JOIN perfil_usuarios pu4 ON pa2.jugador2_id = pu4.id_usuario
    WHERE p.id_torneo = 46
    AND p.categoria_id = 126
    AND p.fase = 'zona'
    ORDER BY p.fecha_hora, p.id_partido
""")

partidos = cur.fetchall()

print("\n" + "="*80)
print("FIXTURE FINAL - TORNEO 46 - CATEGORIA 7MA")
print("="*80 + "\n")

# Agrupar por dia
partidos_viernes = []
partidos_sabado = []
partidos_domingo = []

for p in partidos:
    fecha = p['fecha_hora']
    # La BD guarda en formato que el frontend interpreta como hora local
    # Extraer dia del mes para determinar viernes (28), sabado (29), domingo (30)
    dia = fecha.day
    
    if dia == 28:
        partidos_viernes.append(p)
    elif dia == 29:
        partidos_sabado.append(p)
    else:
        partidos_domingo.append(p)

print(f"VIERNES 28 MARZO ({len(partidos_viernes)} partidos)")
print("-" * 80)
for p in partidos_viernes:
    hora = p['fecha_hora'].strftime('%H:%M')
    print(f"  {hora} | {p['zona_nombre']:8} | {p['pareja1_nombre']} vs {p['pareja2_nombre']}")

print(f"\nSABADO 29 MARZO ({len(partidos_sabado)} partidos)")
print("-" * 80)
for p in partidos_sabado:
    hora = p['fecha_hora'].strftime('%H:%M')
    print(f"  {hora} | {p['zona_nombre']:8} | {p['pareja1_nombre']} vs {p['pareja2_nombre']}")

if partidos_domingo:
    print(f"\nDOMINGO 30 MARZO ({len(partidos_domingo)} partidos)")
    print("-" * 80)
    for p in partidos_domingo:
        hora = p['fecha_hora'].strftime('%H:%M')
        print(f"  {hora} | {p['zona_nombre']:8} | {p['pareja1_nombre']} vs {p['pareja2_nombre']}")

print("\n" + "="*80)
print(f"TOTAL: {len(partidos)} partidos")
print(f"  Viernes: {len(partidos_viernes)}")
print(f"  Sabado: {len(partidos_sabado)}")
print(f"  Domingo: {len(partidos_domingo)}")
print("="*80 + "\n")

# Verificar partidos en horarios indebidos (domingo o sabado tarde)
partidos_indebidos = []
for p in partidos:
    dia = p['fecha_hora'].day
    hora = p['fecha_hora'].hour
    
    if dia == 30:  # Domingo
        partidos_indebidos.append((p, 'Domingo'))
    elif dia == 29 and hora >= 16:  # Sabado tarde
        partidos_indebidos.append((p, 'Sabado tarde (>=16:00)'))

if partidos_indebidos:
    print("ADVERTENCIA - PARTIDOS EN HORARIOS INDEBIDOS:")
    print("-" * 80)
    for p, motivo in partidos_indebidos:
        hora = p['fecha_hora'].strftime('%H:%M')
        print(f"  Partido {p['id_partido']}: {motivo} {hora}")
    print()
else:
    print("OK - Todos los partidos estan en horarios correctos (viernes y sabado temprano)")
    print()

cur.close()
conn.close()
