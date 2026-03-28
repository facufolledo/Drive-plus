import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

load_dotenv('.env.production')

conn = psycopg2.connect(os.getenv('DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://'))
cur = conn.cursor(cursor_factory=RealDictCursor)

TIEMPO_DESCANSO_MINIMO = 180  # 3 horas en minutos

def verificar_solapamientos():
    print("=" * 80)
    print("VERIFICACIÓN EXHAUSTIVA DE SOLAPAMIENTOS Y RESTRICCIONES - TORNEO 46")
    print("=" * 80)
    
    # 1. MOVER PARTIDO 1202 AL VIERNES
    print("\n🔨 Moviendo partido 1202 al viernes...")
    cur.execute("""
        UPDATE partidos
        SET fecha_hora = '2026-03-27 18:00:00'
        WHERE id_partido = 1202
    """)
    conn.commit()
    print("✅ Partido 1202 movido a viernes 27 marzo 18:00")
    
    # 2. OBTENER TODOS LOS PARTIDOS DE 7MA Y 5TA CON HORARIOS
    cur.execute("""
        SELECT 
            p.id_partido,
            p.fecha_hora,
            p.categoria_id,
            tc.nombre as categoria,
            z.nombre as zona,
            p.pareja1_id,
            p.pareja2_id,
            tp1.jugador1_id as j1_p1,
            tp1.jugador2_id as j2_p1,
            tp2.jugador1_id as j1_p2,
            tp2.jugador2_id as j2_p2
        FROM partidos p
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        JOIN torneo_zonas z ON p.zona_id = z.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        WHERE p.id_torneo = 46 
        AND tc.nombre IN ('7ma', '5ta')
        AND p.fecha_hora IS NOT NULL
        ORDER BY p.fecha_hora, p.id_partido
    """)
    
    partidos = cur.fetchall()
    
    print(f"\n📊 Total de partidos programados: {len(partidos)}")
    print(f"   - 7ma: {sum(1 for p in partidos if p['categoria'] == '7ma')}")
    print(f"   - 5ta: {sum(1 for p in partidos if p['categoria'] == '5ta')}")
    
    # 3. VERIFICAR SOLAPAMIENTOS POR JUGADOR
    print("\n" + "=" * 80)
    print("VERIFICANDO SOLAPAMIENTOS POR JUGADOR")
    print("=" * 80)
    
    solapamientos = []
    
    for i, partido1 in enumerate(partidos):
        jugadores_p1 = {partido1['j1_p1'], partido1['j2_p1'], partido1['j1_p2'], partido1['j2_p2']}
        
        for partido2 in partidos[i+1:]:
            jugadores_p2 = {partido2['j1_p1'], partido2['j2_p1'], partido2['j1_p2'], partido2['j2_p2']}
            
            # Verificar si hay jugadores en común
            jugadores_comunes = jugadores_p1 & jugadores_p2
            
            if jugadores_comunes:
                # Calcular diferencia de tiempo
                diff_minutos = abs((partido2['fecha_hora'] - partido1['fecha_hora']).total_seconds() / 60)
                
                if diff_minutos < TIEMPO_DESCANSO_MINIMO:
                    solapamientos.append({
                        'partido1': partido1,
                        'partido2': partido2,
                        'jugadores_comunes': jugadores_comunes,
                        'diff_minutos': diff_minutos
                    })
    
    if solapamientos:
        print(f"\n❌ ENCONTRADOS {len(solapamientos)} SOLAPAMIENTOS:\n")
        for solap in solapamientos:
            p1 = solap['partido1']
            p2 = solap['partido2']
            print(f"⚠️  Partido {p1['id_partido']} ({p1['categoria']} - {p1['zona']}) a las {p1['fecha_hora'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   vs")
            print(f"   Partido {p2['id_partido']} ({p2['categoria']} - {p2['zona']}) a las {p2['fecha_hora'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Diferencia: {solap['diff_minutos']:.0f} minutos (mínimo requerido: {TIEMPO_DESCANSO_MINIMO})")
            print(f"   Jugadores en común: {solap['jugadores_comunes']}")
            print()
    else:
        print("\n✅ NO HAY SOLAPAMIENTOS - Todos los jugadores tienen al menos 3 horas de descanso")
    
    # 4. VERIFICAR RESTRICCIONES
    print("\n" + "=" * 80)
    print("VERIFICANDO RESTRICCIONES DE DISPONIBILIDAD")
    print("=" * 80)
    
    violaciones_restricciones = []
    
    for partido in partidos:
        # Obtener restricciones de ambas parejas
        cur.execute("""
            SELECT disponibilidad_horaria
            FROM torneos_parejas
            WHERE id IN (%s, %s)
        """, (partido['pareja1_id'], partido['pareja2_id']))
        
        restricciones = cur.fetchall()
        
        for rest_row in restricciones:
            if rest_row['disponibilidad_horaria']:
                restricciones_data = rest_row['disponibilidad_horaria']
                
                # Verificar si el horario del partido viola alguna restricción
                fecha_partido = partido['fecha_hora']
                dia_semana = fecha_partido.strftime('%A').lower()
                dia_map = {
                    'monday': 'lunes', 'tuesday': 'martes', 'wednesday': 'miércoles',
                    'thursday': 'jueves', 'friday': 'viernes', 'saturday': 'sábado', 'sunday': 'domingo'
                }
                dia_es = dia_map.get(dia_semana, dia_semana)
                
                hora_partido = fecha_partido.strftime('%H:%M')
                
                for restriccion in restricciones_data:
                    if dia_es in restriccion.get('dias', []):
                        hora_inicio = restriccion.get('horaInicio', '00:00')
                        hora_fin = restriccion.get('horaFin', '23:59')
                        
                        if hora_inicio <= hora_partido <= hora_fin:
                            violaciones_restricciones.append({
                                'partido': partido,
                                'restriccion': restriccion
                            })
    
    if violaciones_restricciones:
        print(f"\n❌ ENCONTRADAS {len(violaciones_restricciones)} VIOLACIONES DE RESTRICCIONES:\n")
        for viol in violaciones_restricciones:
            p = viol['partido']
            r = viol['restriccion']
            print(f"⚠️  Partido {p['id_partido']} ({p['categoria']} - {p['zona']}) a las {p['fecha_hora'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Restricción: {r}")
            print()
    else:
        print("\n✅ NO HAY VIOLACIONES DE RESTRICCIONES")
    
    # 5. RESUMEN POR DÍA Y CATEGORÍA
    print("\n" + "=" * 80)
    print("RESUMEN DE DISTRIBUCIÓN")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            tc.nombre as categoria,
            CASE 
                WHEN EXTRACT(DAY FROM p.fecha_hora) = 27 THEN 'Viernes 27'
                WHEN EXTRACT(DAY FROM p.fecha_hora) = 28 THEN 'Sábado 28'
                ELSE 'Otro'
            END as dia,
            COUNT(*) as total
        FROM partidos p
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        WHERE p.id_torneo = 46 
        AND tc.nombre IN ('7ma', '5ta')
        AND p.fecha_hora IS NOT NULL
        GROUP BY tc.nombre, dia
        ORDER BY tc.nombre, dia
    """)
    
    print("\n📊 Distribución de partidos:")
    for row in cur.fetchall():
        print(f"   {row['categoria']} - {row['dia']}: {row['total']} partidos")
    
    # 6. PARTIDOS SIN HORARIO
    cur.execute("""
        SELECT 
            tc.nombre as categoria,
            COUNT(*) as total
        FROM partidos p
        JOIN torneo_categorias tc ON p.categoria_id = tc.id
        WHERE p.id_torneo = 46 
        AND tc.nombre IN ('7ma', '5ta')
        AND p.fecha_hora IS NULL
        GROUP BY tc.nombre
    """)
    
    sin_horario = cur.fetchall()
    if sin_horario:
        print("\n⚠️  Partidos SIN horario asignado:")
        for row in sin_horario:
            print(f"   {row['categoria']}: {row['total']} partidos")
    
    print("\n" + "=" * 80)
    print("VERIFICACIÓN COMPLETADA")
    print("=" * 80)
    
    return len(solapamientos) == 0 and len(violaciones_restricciones) == 0

try:
    resultado = verificar_solapamientos()
    if resultado:
        print("\n✅ TODO CORRECTO - No hay solapamientos ni violaciones de restricciones")
    else:
        print("\n❌ HAY PROBLEMAS QUE REQUIEREN ATENCIÓN")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
