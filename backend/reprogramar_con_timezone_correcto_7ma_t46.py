"""
Reprogramar TODOS los partidos de 7ma considerando timezone Argentina (UTC-3)
Los horarios en BD están en UTC, pero las restricciones son en hora local
"""
import sys, os
from datetime import datetime, timedelta, time
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine, text
import json

env_file = os.path.join(os.path.dirname(__file__), '.env.production')
DATABASE_URL = None
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DATABASE_URL = line.split('=', 1)[1].strip().strip('"').strip("'")
                break

engine = create_engine(DATABASE_URL)

TORNEO_ID = 46

def verificar_disponibilidad_pareja(restricciones, fecha_hora_utc):
    """Verifica si una pareja puede jugar en un horario dado (considerando UTC-3)"""
    if not restricciones:
        return True
    
    # Convertir UTC a hora local Argentina (UTC-3)
    hora_local = fecha_hora_utc - timedelta(hours=3)
    
    dia_semana = hora_local.strftime('%A').lower()
    dia_map = {
        'friday': 'viernes',
        'saturday': 'sabado',
        'sunday': 'domingo'
    }
    dia_esp = dia_map.get(dia_semana, dia_semana)
    hora_str = hora_local.strftime('%H:%M')
    
    for restr in restricciones:
        if dia_esp in restr.get('dias', []):
            hora_inicio = restr.get('horaInicio', '00:00')
            hora_fin = restr.get('horaFin', '23:59')
            
            if hora_inicio <= hora_str <= hora_fin:
                return False  # Está en una restricción (NO disponible)
    
    return True

def generar_slots_horarios_utc(fecha_base_local, hora_inicio_local, hora_fin_local, intervalo_min=70):
    """Genera slots en UTC a partir de horarios locales"""
    slots = []
    
    # Convertir hora local a UTC (+3 horas)
    hora_actual_local = datetime.combine(fecha_base_local, hora_inicio_local)
    hora_limite_local = datetime.combine(fecha_base_local, hora_fin_local)
    
    while hora_actual_local <= hora_limite_local:
        # Convertir a UTC
        hora_utc = hora_actual_local + timedelta(hours=3)
        slots.append(hora_utc)
        hora_actual_local += timedelta(minutes=intervalo_min)
    
    return slots

def main():
    print("=" * 80)
    print("REPROGRAMANDO TODOS LOS PARTIDOS 7MA CON TIMEZONE CORRECTO")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Obtener categoria_id
        cat = conn.execute(text("""
            SELECT id FROM torneo_categorias WHERE torneo_id = :tid AND nombre = '7ma'
        """), {"tid": TORNEO_ID}).fetchone()
        
        if not cat:
            print("❌ ERROR: Categoría 7ma no encontrada")
            return
        
        CATEGORIA_ID = cat.id
        
        # Obtener fecha del torneo
        torneo = conn.execute(text("""
            SELECT fecha_inicio FROM torneos WHERE id = :tid
        """), {"tid": TORNEO_ID}).fetchone()
        
        viernes_local = torneo.fecha_inicio
        sabado_local = viernes_local + timedelta(days=1)
        
        print(f"\n📅 Fechas locales (Argentina):")
        print(f"  Viernes: {viernes_local}")
        print(f"  Sábado: {sabado_local}")
        
        # Generar slots en hora local y convertir a UTC
        # Viernes: 14:00 - 23:59 cada 70 min
        # Sábado: 08:00 - 15:59 cada 70 min
        slots_viernes_utc = generar_slots_horarios_utc(viernes_local, time(14, 0), time(23, 59), 70)
        slots_sabado_utc = generar_slots_horarios_utc(sabado_local, time(8, 0), time(15, 59), 70)
        
        todos_slots_utc = slots_viernes_utc + slots_sabado_utc
        
        print(f"\n📅 SLOTS GENERADOS (en UTC para BD): {len(todos_slots_utc)}")
        print(f"  Viernes: {len(slots_viernes_utc)} slots")
        print(f"  Sábado: {len(slots_sabado_utc)} slots")
        
        # Obtener todos los partidos
        partidos = conn.execute(text("""
            SELECT p.id_partido, p.fecha_hora, p.pareja1_id, p.pareja2_id,
                   tp1.disponibilidad_horaria as restr1,
                   tp2.disponibilidad_horaria as restr2
            FROM partidos p
            LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            WHERE p.id_torneo = :tid AND p.categoria_id = :cid
            ORDER BY p.id_partido
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        print(f"\n📊 Total partidos a reprogramar: {len(partidos)}")
        
        print("\n" + "=" * 80)
        print("REPROGRAMANDO PARTIDOS")
        print("=" * 80)
        
        movidos = 0
        no_movidos = []
        
        for partido in partidos:
            restr1 = partido.restr1 if partido.restr1 else []
            restr2 = partido.restr2 if partido.restr2 else []
            
            # Buscar primer horario disponible
            nuevo_horario_utc = None
            
            for slot_utc in todos_slots_utc:
                # 1. Verificar restricciones de ambas parejas
                if not verificar_disponibilidad_pareja(restr1, slot_utc):
                    continue
                
                if not verificar_disponibilidad_pareja(restr2, slot_utc):
                    continue
                
                # 2. Verificar solapamiento
                solapamiento = conn.execute(text("""
                    SELECT COUNT(*) FROM partidos p
                    WHERE p.id_torneo = :tid 
                      AND p.categoria_id = :cid
                      AND p.id_partido != :pid
                      AND p.fecha_hora = :fh
                      AND (p.pareja1_id IN (:p1, :p2) OR p.pareja2_id IN (:p1, :p2))
                """), {
                    "tid": TORNEO_ID,
                    "cid": CATEGORIA_ID,
                    "pid": partido.id_partido,
                    "fh": slot_utc,
                    "p1": partido.pareja1_id,
                    "p2": partido.pareja2_id
                }).fetchone()[0]
                
                if solapamiento == 0:
                    nuevo_horario_utc = slot_utc
                    break
            
            if nuevo_horario_utc:
                # Actualizar partido
                conn.execute(text("""
                    UPDATE partidos 
                    SET fecha_hora = :fh
                    WHERE id_partido = :pid
                """), {"fh": nuevo_horario_utc, "pid": partido.id_partido})
                
                hora_local = nuevo_horario_utc - timedelta(hours=3)
                if movidos < 5:  # Mostrar solo primeros 5
                    print(f"✅ Partido {partido.id_partido}: {nuevo_horario_utc} UTC → {hora_local} ARG")
                movidos += 1
            else:
                no_movidos.append(partido.id_partido)
                print(f"❌ Partido {partido.id_partido}: No se encontró horario válido")
        
        conn.commit()
        
        print(f"\n... ({movidos} partidos movidos en total)")
        
        print("\n" + "=" * 80)
        print(f"✅ {movidos}/{len(partidos)} PARTIDOS REPROGRAMADOS")
        print("=" * 80)
        
        if no_movidos:
            print(f"\n⚠️  {len(no_movidos)} partidos NO pudieron moverse:")
            for pid in no_movidos:
                print(f"  - Partido {pid}")
        
        # Verificación final
        print("\n📊 VERIFICACIÓN FINAL (HORA LOCAL ARGENTINA):")
        
        partidos_final = conn.execute(text("""
            SELECT id_partido, fecha_hora, pareja1_id, pareja2_id,
                   tp1.disponibilidad_horaria as restr1,
                   tp2.disponibilidad_horaria as restr2
            FROM partidos p
            LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            WHERE p.id_torneo = :tid AND p.categoria_id = :cid
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        viernes_count = 0
        sabado_temprano = 0
        sabado_tarde = 0
        domingo_count = 0
        violaciones = 0
        
        for p in partidos_final:
            hora_local = p.fecha_hora - timedelta(hours=3)
            dia = hora_local.strftime('%A')
            hora = hora_local.hour
            
            if dia == 'Friday':
                viernes_count += 1
            elif dia == 'Saturday':
                if hora < 16:
                    sabado_temprano += 1
                else:
                    sabado_tarde += 1
            elif dia == 'Sunday':
                domingo_count += 1
            
            # Verificar restricciones
            ok1 = verificar_disponibilidad_pareja(p.restr1, p.fecha_hora)
            ok2 = verificar_disponibilidad_pareja(p.restr2, p.fecha_hora)
            if not ok1 or not ok2:
                violaciones += 1
        
        print(f"  ✅ Viernes: {viernes_count} partidos")
        print(f"  ✅ Sábado temprano (<16:00): {sabado_temprano} partidos")
        if sabado_tarde > 0:
            print(f"  ❌ Sábado tarde (>=16:00): {sabado_tarde} partidos")
        if domingo_count > 0:
            print(f"  ❌ Domingo: {domingo_count} partidos")
        
        if violaciones > 0:
            print(f"\n  ❌ {violaciones} partidos violan restricciones")
        else:
            print(f"\n  ✅ Todos los partidos respetan restricciones")

if __name__ == "__main__":
    main()
