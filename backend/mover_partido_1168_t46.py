import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 80)
print("ANÁLISIS PARTIDO 1168 - TORNEO 46")
print("=" * 80)

# Ver información del partido 1168
cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        tc.nombre as categoria,
        z.nombre as zona,
        p.pareja1_id,
        p.pareja2_id,
        pu1.nombre || ' ' || pu1.apellido as p1_j1,
        pu2.nombre || ' ' || pu2.apellido as p1_j2,
        pu3.nombre || ' ' || pu3.apellido as p2_j1,
        pu4.nombre || ' ' || pu4.apellido as p2_j2,
        tp1.jugador1_id as j1_p1,
        tp1.jugador2_id as j2_p1,
        tp2.jugador1_id as j1_p2,
        tp2.jugador2_id as j2_p2,
        tp1.disponibilidad_horaria as rest_p1,
        tp2.disponibilidad_horaria as rest_p2
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    JOIN torneo_zonas z ON p.zona_id = z.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    JOIN perfil_usuarios pu1 ON tp1.jugador1_id = pu1.id_usuario
    JOIN perfil_usuarios pu2 ON tp1.jugador2_id = pu2.id_usuario
    JOIN perfil_usuarios pu3 ON tp2.jugador1_id = pu3.id_usuario
    JOIN perfil_usuarios pu4 ON tp2.jugador2_id = pu4.id_usuario
    WHERE p.id_partido = 1168
""")

partido = cur.fetchone()

if not partido:
    print("❌ Partido 1168 no encontrado")
    cur.close()
    conn.close()
    exit(1)

print(f"\n📋 PARTIDO 1168:")
print(f"  Categoría: {partido['categoria']}")
print(f"  Zona: {partido['zona']}")
if partido['fecha_hora']:
    dia = 'Viernes' if partido['fecha_hora'].day == 27 else 'Sábado'
    print(f"  Horario actual: {dia} {partido['fecha_hora'].strftime('%H:%M')}")
else:
    print(f"  Horario actual: SIN HORARIO")
print(f"  Pareja 1: {partido['p1_j1']} / {partido['p1_j2']}")
print(f"  Pareja 2: {partido['p2_j1']} / {partido['p2_j2']}")

# Ver restricciones de ambas parejas
print(f"\n📋 RESTRICCIONES:")
print(f"\n  Pareja {partido['pareja1_id']} ({partido['p1_j1']} / {partido['p1_j2']}):")
if partido['rest_p1']:
    for r in partido['rest_p1']:
        dias = ', '.join(r.get('dias', []))
        print(f"    NO disponible {dias} de {r.get('horaInicio')} a {r.get('horaFin')}")
else:
    print("    Sin restricciones")

print(f"\n  Pareja {partido['pareja2_id']} ({partido['p2_j1']} / {partido['p2_j2']}):")
if partido['rest_p2']:
    for r in partido['rest_p2']:
        dias = ', '.join(r.get('dias', []))
        print(f"    NO disponible {dias} de {r.get('horaInicio')} a {r.get('horaFin')}")
else:
    print("    Sin restricciones")

# Ver otros partidos de los jugadores involucrados
jugadores_ids = [partido['j1_p1'], partido['j2_p1'], partido['j1_p2'], partido['j2_p2']]

cur.execute("""
    SELECT 
        p.id_partido,
        p.fecha_hora,
        tc.nombre as categoria,
        z.nombre as zona
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    JOIN torneo_zonas z ON p.zona_id = z.id
    JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
    JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
    WHERE p.id_torneo = 46
    AND p.id_partido != 1168
    AND p.fecha_hora IS NOT NULL
    AND (tp1.jugador1_id = ANY(%s) OR tp1.jugador2_id = ANY(%s) 
         OR tp2.jugador1_id = ANY(%s) OR tp2.jugador2_id = ANY(%s))
    ORDER BY p.fecha_hora
""", (jugadores_ids, jugadores_ids, jugadores_ids, jugadores_ids))

otros_partidos = cur.fetchall()

print(f"\n📅 OTROS PARTIDOS DE ESTOS JUGADORES:")
for p in otros_partidos:
    dia = 'Viernes' if p['fecha_hora'].day == 27 else 'Sábado'
    print(f"  Partido {p['id_partido']}: {dia} {p['fecha_hora'].strftime('%H:%M')} - {p['categoria']} - {p['zona']}")

# Ver horarios disponibles después de sábado 14:30
print(f"\n" + "=" * 80)
print("HORARIOS DISPONIBLES DESPUÉS DE SÁBADO 14:30")
print("=" * 80)

cur.execute("""
    SELECT 
        p.fecha_hora,
        COUNT(*) as partidos
    FROM partidos p
    JOIN torneo_categorias tc ON p.categoria_id = tc.id
    WHERE p.id_torneo = 46
    AND tc.nombre IN ('7ma', '5ta')
    AND p.fecha_hora IS NOT NULL
    AND p.fecha_hora >= '2026-03-28 14:30:00'
    GROUP BY p.fecha_hora
    ORDER BY p.fecha_hora
""")

horarios_ocupados = {h['fecha_hora']: h['partidos'] for h in cur.fetchall()}

# Generar horarios candidatos (cada 30 minutos desde 14:30 hasta 23:30)
from datetime import datetime, timedelta

horarios_candidatos = []
hora_inicio = datetime(2026, 3, 28, 14, 30)  # Sábado 14:30
hora_fin = datetime(2026, 3, 28, 23, 30)

hora_actual = hora_inicio
while hora_actual <= hora_fin:
    horarios_candidatos.append(hora_actual)
    hora_actual += timedelta(minutes=30)

print("\n📊 OCUPACIÓN DE HORARIOS:")
for h in horarios_candidatos:
    ocupacion = horarios_ocupados.get(h, 0)
    print(f"  {h.strftime('%H:%M')}: {ocupacion} partido(s)")

# Función para verificar si un horario respeta restricciones
def verifica_restricciones(fecha_hora, restricciones):
    if not restricciones:
        return True
    
    dia_semana = fecha_hora.strftime('%A').lower()
    dia_map = {
        'monday': 'lunes', 'tuesday': 'martes', 'wednesday': 'miércoles',
        'thursday': 'jueves', 'friday': 'viernes', 'saturday': 'sábado', 'sunday': 'domingo'
    }
    dia_es = dia_map.get(dia_semana, dia_semana)
    hora = fecha_hora.strftime('%H:%M')
    
    for r in restricciones:
        if dia_es in r.get('dias', []):
            hora_inicio = r.get('horaInicio', '00:00')
            hora_fin = r.get('horaFin', '23:59')
            if hora_inicio <= hora <= hora_fin:
                return False
    
    return True

# Función para verificar solapamientos con otros partidos
def verifica_solapamientos(fecha_hora, otros_partidos_list):
    for p in otros_partidos_list:
        diff_minutos = abs((fecha_hora - p['fecha_hora']).total_seconds() / 60)
        if diff_minutos < 90:  # Menos de 90 minutos es problemático
            return False
    return True

# Buscar el mejor horario
print(f"\n" + "=" * 80)
print("ANÁLISIS DE HORARIOS CANDIDATOS")
print("=" * 80)

mejor_horario = None
for h in horarios_candidatos:
    respeta_p1 = verifica_restricciones(h, partido['rest_p1'])
    respeta_p2 = verifica_restricciones(h, partido['rest_p2'])
    sin_solapamiento = verifica_solapamientos(h, otros_partidos)
    ocupacion = horarios_ocupados.get(h, 0)
    
    print(f"\n  {h.strftime('%H:%M')}:")
    print(f"    Restricciones P1: {'✅' if respeta_p1 else '❌'}")
    print(f"    Restricciones P2: {'✅' if respeta_p2 else '❌'}")
    print(f"    Sin solapamiento: {'✅' if sin_solapamiento else '❌'}")
    print(f"    Ocupación: {ocupacion} partido(s)")
    
    if respeta_p1 and respeta_p2 and sin_solapamiento:
        if mejor_horario is None or ocupacion < horarios_ocupados.get(mejor_horario, 999):
            mejor_horario = h
            print(f"    ⭐ CANDIDATO")

if mejor_horario:
    print(f"\n" + "=" * 80)
    print(f"✅ MEJOR HORARIO ENCONTRADO: Sábado {mejor_horario.strftime('%H:%M')}")
    print("=" * 80)
    
    # Actualizar el partido
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = %s
        WHERE id_partido = 1168
    """, (mejor_horario,))
    
    conn.commit()
    print(f"\n✅ Partido 1168 actualizado a sábado {mejor_horario.strftime('%H:%M')}")
else:
    print(f"\n❌ No se encontró un horario válido después de sábado 14:30")

cur.close()
conn.close()
