"""
Script para corregir TODOS los partidos de 7ma torneo 46 con timezone correcto.

REGLA CRÍTICA:
- La BD guarda timestamps que el frontend interpreta como hora LOCAL Argentina
- Si queremos mostrar 15:00 en Argentina, guardamos '2026-03-28 15:00:00' en BD
- NO hay conversión de timezone, el frontend lee los valores UTC como hora local

OBJETIVO:
- Partidos de ZONA deben jugarse viernes y sábado temprano (<16:00)
- Validar restricciones usando hora local Argentina
- Evitar solapamientos
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Cargar variables de entorno de producción
load_dotenv('.env.production')

def conectar_db():
    db_url = os.getenv('DATABASE_URL')
    # Convertir postgresql+pg8000:// a postgresql://
    if db_url.startswith('postgresql+pg8000://'):
        db_url = db_url.replace('postgresql+pg8000://', 'postgresql://')
    return psycopg2.connect(db_url)

def listar_partidos_7ma():
    """Lista todos los partidos de 7ma con su info completa"""
    conn = conectar_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
    SELECT 
        p.id_partido as id,
        p.fecha_hora,
        p.fase,
        p.zona_id,
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
    WHERE p.id_torneo = 46
    AND p.categoria_id = 126
    AND p.fase = 'zona'
    ORDER BY p.id_partido
    """
    
    cur.execute(query)
    partidos = cur.fetchall()
    cur.close()
    conn.close()
    
    return partidos

def parsear_restricciones(disponibilidad_json):
    """Parsea las restricciones (horarios NO disponibles)"""
    if not disponibilidad_json:
        return []
    
    restricciones = []
    for item in disponibilidad_json:
        dias = item.get('dias', [])
        hora_inicio = item.get('horaInicio', '00:00')
        hora_fin = item.get('horaFin', '23:59')
        restricciones.append({
            'dias': dias,
            'hora_inicio': hora_inicio,
            'hora_fin': hora_fin
        })
    
    return restricciones

def hora_viola_restricciones(dia_semana, hora_str, restricciones):
    """Verifica si un horario viola las restricciones de una pareja"""
    if not restricciones:
        return False
    
    # Mapeo de días
    dias_map = {
        'viernes': ['viernes'],
        'sabado': ['sabado', 'sábado'],
        'domingo': ['domingo']
    }
    
    for rest in restricciones:
        # Verificar si el día está en la restricción
        dias_rest = rest['dias']
        if dia_semana in dias_map:
            if any(d in dias_rest for d in dias_map[dia_semana]):
                # Verificar si la hora está en el rango restringido
                hora_inicio = rest['hora_inicio']
                hora_fin = rest['hora_fin']
                
                if hora_inicio <= hora_str <= hora_fin:
                    return True
    
    return False

def generar_slots_disponibles():
    """Genera slots de horarios válidos para partidos de zona"""
    slots = []
    
    # Viernes 28 marzo 2026: 16:00 a 23:30 (cada 1.5 horas)
    fecha_viernes = datetime(2026, 3, 28)
    horas_viernes = ['16:00', '17:30', '19:00', '20:30', '22:00', '23:30']
    for hora in horas_viernes:
        h, m = map(int, hora.split(':'))
        slots.append({
            'fecha': fecha_viernes.replace(hour=h, minute=m),
            'dia_semana': 'viernes',
            'hora_str': hora
        })
    
    # Sábado 29 marzo 2026: 08:00 a 15:30 (cada 1.5 horas)
    fecha_sabado = datetime(2026, 3, 29)
    horas_sabado = ['08:00', '09:30', '11:00', '12:30', '14:00', '15:30']
    for hora in horas_sabado:
        h, m = map(int, hora.split(':'))
        slots.append({
            'fecha': fecha_sabado.replace(hour=h, minute=m),
            'dia_semana': 'sabado',
            'hora_str': hora
        })
    
    return slots

def encontrar_mejor_horario(partido, slots_usados):
    """Encuentra el mejor horario para un partido validando restricciones"""
    pareja1_rest = parsear_restricciones(partido['pareja1_disponibilidad'])
    pareja2_rest = parsear_restricciones(partido['pareja2_disponibilidad'])
    
    slots = generar_slots_disponibles()
    
    for slot in slots:
        # Verificar si el slot ya está usado por alguna de las parejas
        slot_key = slot['fecha'].isoformat()
        if partido['pareja1_id'] in slots_usados.get(slot_key, []):
            continue
        if partido['pareja2_id'] in slots_usados.get(slot_key, []):
            continue
        
        # Verificar restricciones de ambas parejas
        viola_p1 = hora_viola_restricciones(slot['dia_semana'], slot['hora_str'], pareja1_rest)
        viola_p2 = hora_viola_restricciones(slot['dia_semana'], slot['hora_str'], pareja2_rest)
        
        if not viola_p1 and not viola_p2:
            return slot
    
    return None

def reprogramar_partidos():
    """Reprograma todos los partidos de 7ma validando restricciones"""
    partidos = listar_partidos_7ma()
    
    print(f"\n{'='*80}")
    print(f"REPROGRAMACIÓN COMPLETA - TORNEO 46 - CATEGORÍA 7MA")
    print(f"{'='*80}\n")
    print(f"Total partidos a reprogramar: {len(partidos)}\n")
    
    # Diccionario para trackear slots usados por pareja
    slots_usados = {}  # {fecha_iso: [pareja_id1, pareja_id2, ...]}
    
    actualizaciones = []
    partidos_sin_horario = []
    
    for partido in partidos:
        print(f"\n{'─'*80}")
        print(f"Partido {partido['id']}: {partido['zona_nombre']}")
        print(f"  {partido['pareja1_nombre']} vs {partido['pareja2_nombre']}")
        print(f"  Horario actual: {partido['fecha_hora']}")
        
        # Buscar mejor horario
        mejor_slot = encontrar_mejor_horario(partido, slots_usados)
        
        if mejor_slot:
            nueva_fecha = mejor_slot['fecha']
            
            # Marcar slot como usado
            slot_key = nueva_fecha.isoformat()
            if slot_key not in slots_usados:
                slots_usados[slot_key] = []
            slots_usados[slot_key].append(partido['pareja1_id'])
            slots_usados[slot_key].append(partido['pareja2_id'])
            
            actualizaciones.append({
                'partido_id': partido['id'],
                'nueva_fecha': nueva_fecha,
                'dia_semana': mejor_slot['dia_semana'],
                'hora': mejor_slot['hora_str']
            })
            
            print(f"  ✅ NUEVO HORARIO: {mejor_slot['dia_semana'].upper()} {nueva_fecha.strftime('%d/%m/%Y')} {mejor_slot['hora_str']}")
        else:
            partidos_sin_horario.append(partido)
            print(f"  ❌ NO SE ENCONTRÓ HORARIO COMPATIBLE")
    
    # Mostrar resumen
    print(f"\n{'='*80}")
    print(f"RESUMEN")
    print(f"{'='*80}\n")
    print(f"✅ Partidos con nuevo horario: {len(actualizaciones)}")
    print(f"❌ Partidos sin horario compatible: {len(partidos_sin_horario)}")
    
    if partidos_sin_horario:
        print(f"\n⚠️  PARTIDOS SIN HORARIO:")
        for p in partidos_sin_horario:
            print(f"  - Partido {p['id']}: {p['pareja1_nombre']} vs {p['pareja2_nombre']}")
    
    # Confirmar ejecución
    if actualizaciones:
        print(f"\n{'='*80}")
        respuesta = input(f"\n¿Ejecutar {len(actualizaciones)} actualizaciones en BD? (si/no): ")
        
        if respuesta.lower() == 'si':
            conn = conectar_db()
            cur = conn.cursor()
            
            for act in actualizaciones:
                query = """
                UPDATE partidos 
                SET fecha_hora = %s
                WHERE id_partido = %s
                """
                cur.execute(query, (act['nueva_fecha'], act['partido_id']))
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"\n✅ {len(actualizaciones)} partidos actualizados exitosamente")
        else:
            print("\n❌ Operación cancelada")
    else:
        print("\n⚠️  No hay actualizaciones para ejecutar")

if __name__ == '__main__':
    reprogramar_partidos()
