"""Analizar por qué 5 partidos no encuentran horario compatible"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import json

load_dotenv('.env.production')

def conectar_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url.startswith('postgresql+pg8000://'):
        db_url = db_url.replace('postgresql+pg8000://', 'postgresql://')
    return psycopg2.connect(db_url)

partidos_problematicos = [1044, 1045, 1046, 1052, 1061]

conn = conectar_db()
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "="*80)
print("ANÁLISIS DE PARTIDOS SIN HORARIO COMPATIBLE")
print("="*80 + "\n")

for partido_id in partidos_problematicos:
    cur.execute("""
        SELECT 
            p.id_partido,
            z.nombre as zona_nombre,
            pa1.id as pareja1_id,
            pu1.nombre || ' ' || pu1.apellido || ' / ' || pu2.nombre || ' ' || pu2.apellido as pareja1_nombre,
            pa1.disponibilidad_horaria as pareja1_disponibilidad,
            pa2.id as pareja2_id,
            pu3.nombre || ' ' || pu3.apellido || ' / ' || pu4.nombre || ' ' || pu4.apellido as pareja2_nombre,
            pa2.disponibilidad_horaria as pareja2_disponibilidad
        FROM partidos p
        LEFT JOIN torneo_zonas z ON p.zona_id = z.id
        LEFT JOIN torneos_parejas pa1 ON p.pareja1_id = pa1.id
        LEFT JOIN perfil_usuarios pu1 ON pa1.jugador1_id = pu1.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON pa1.jugador2_id = pu2.id_usuario
        LEFT JOIN torneos_parejas pa2 ON p.pareja2_id = pa2.id
        LEFT JOIN perfil_usuarios pu3 ON pa2.jugador1_id = pu3.id_usuario
        LEFT JOIN perfil_usuarios pu4 ON pa2.jugador2_id = pu4.id_usuario
        WHERE p.id_partido = %s
    """, (partido_id,))
    
    partido = cur.fetchone()
    
    print(f"{'─'*80}")
    print(f"PARTIDO {partido['id_partido']}: {partido['zona_nombre']}")
    print(f"{'─'*80}")
    print(f"\n{partido['pareja1_nombre']}")
    print(f"  Restricciones (NO disponibles):")
    if partido['pareja1_disponibilidad']:
        for rest in partido['pareja1_disponibilidad']:
            dias = ', '.join(rest.get('dias', []))
            print(f"    - {dias}: {rest.get('horaInicio')} a {rest.get('horaFin')}")
    else:
        print(f"    - Sin restricciones")
    
    print(f"\nvs\n")
    print(f"{partido['pareja2_nombre']}")
    print(f"  Restricciones (NO disponibles):")
    if partido['pareja2_disponibilidad']:
        for rest in partido['pareja2_disponibilidad']:
            dias = ', '.join(rest.get('dias', []))
            print(f"    - {dias}: {rest.get('horaInicio')} a {rest.get('horaFin')}")
    else:
        print(f"    - Sin restricciones")
    
    print(f"\n{'─'*80}\n")

cur.close()
conn.close()

print("\n" + "="*80)
print("HORARIOS DISPONIBLES DEL TORNEO")
print("="*80)
print("\nViernes 28/03: 18:00, 19:30, 21:00, 22:30")
print("Sábado 29/03: 08:00, 09:30, 11:00, 12:30, 14:00, 15:30")
print("\n" + "="*80 + "\n")
