#!/usr/bin/env python3
"""
Buscar partido de Lucero/Paez a las 22:00 y encontrar intercambio viable
"""
import sys, os, json
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

PAREJA_LUCERO_PAEZ = 822
TORNEO_ID = 45

def parse_restricciones(r):
    if not r:
        return []
    return r if isinstance(r, list) else json.loads(r)

def puede_jugar_horario(restricciones, dia_semana, hora_local):
    """Verifica si una pareja puede jugar en un horario dado sus restricciones"""
    if not restricciones:
        return True
    
    dias_map = {
        'jueves': 3,
        'viernes': 4,
        'sábado': 5,
        'sabado': 5,
        'domingo': 6
    }
    
    for r in restricciones:
        dia_r = r.get('dia', '').lower()
        if dia_r not in dias_map:
            continue
        
        if dias_map[dia_r] != dia_semana:
            continue
        
        # Tiene restricción para este día
        hora_inicio = r.get('horaInicio', '00:00')
        hora_fin = r.get('horaFin', '23:59')
        
        # Si el horario está fuera del rango permitido, NO puede jugar
        if hora_local < hora_inicio or hora_local > hora_fin:
            return False
    
    return True

def main():
    s = Session()
    try:
        print("=" * 80)
        print("BUSCAR INTERCAMBIO PARA LUCERO/PAEZ (PARTIDO A LAS 22:00)")
        print("=" * 80)
        
        # Buscar partido de Lucero/Paez a las 22:00
        partido_22 = s.execute(text("""
            SELECT 
                p.id_partido as id,
                p.pareja1_id,
                p.pareja2_id,
                p.fecha_hora,
                p.cancha_id,
                tp1.nombre_pareja as pareja1_nombre,
                tp2.nombre_pareja as pareja2_nombre,
                tp1.disponibilidad_horaria as p1_restricciones,
                tp2.disponibilidad_horaria as p2_restricciones
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            WHERE tp1.torneo_id = :tid
            AND (p.pareja1_id = :pid OR p.pareja2_id = :pid)
            AND EXTRACT(HOUR FROM p.fecha_hora) = 22
            ORDER BY p.fecha_hora
        """), {"tid": TORNEO_ID, "pid": PAREJA_LUCERO_PAEZ}).fetchone()
        
        if not partido_22:
            print("\n❌ No se encontró partido de Lucero/Paez a las 22:00")
            return
        
        fecha_hora = partido_22.fecha_hora
        dia_semana = fecha_hora.weekday()
        hora_local = fecha_hora.strftime("%H:%M")
        
        print(f"\n📍 PARTIDO ENCONTRADO:")
        print(f"   ID: {partido_22.id}")
        print(f"   {partido_22.pareja1_nombre} vs {partido_22.pareja2_nombre}")
        print(f"   Fecha: {fecha_hora.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Cancha: {partido_22.cancha_id}")
        
        # Obtener restricciones de ambas parejas del partido a las 22
        p1_rest = parse_restricciones(partido_22.p1_restricciones)
        p2_rest = parse_restricciones(partido_22.p2_restricciones)
        
        print(f"\n📋 Restricciones parejas del partido a las 22:")
        print(f"   {partido_22.pareja1_nombre}: {json.dumps(p1_rest, ensure_ascii=False)}")
        print(f"   {partido_22.pareja2_nombre}: {json.dumps(p2_rest, ensure_ascii=False)}")
        
        # Obtener restricciones de Lucero/Paez
        lucero_paez = s.execute(text("""
            SELECT disponibilidad_horaria, nombre_pareja
            FROM torneos_parejas
            WHERE id = :pid
        """), {"pid": PAREJA_LUCERO_PAEZ}).fetchone()
        
        lp_rest = parse_restricciones(lucero_paez.disponibilidad_horaria)
        print(f"\n📋 Restricciones Lucero/Paez:")
        print(f"   {json.dumps(lp_rest, ensure_ascii=False)}")
        
        # Buscar partidos candidatos para intercambio
        # Deben ser partidos donde AMBAS parejas del partido a las 22 puedan jugar
        # Y donde Lucero/Paez también pueda jugar
        print(f"\n🔍 Buscando partidos candidatos para intercambio...")
        
        candidatos = s.execute(text("""
            SELECT 
                p.id_partido as id,
                p.pareja1_id,
                p.pareja2_id,
                p.fecha_hora,
                p.cancha_id,
                tp1.nombre_pareja as pareja1_nombre,
                tp2.nombre_pareja as pareja2_nombre,
                tp1.disponibilidad_horaria as p1_restricciones,
                tp2.disponibilidad_horaria as p2_restricciones
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            WHERE tp1.torneo_id = :tid
            AND p.id_partido != :pid_excluir
            AND p.pareja1_id != :pareja_lucero
            AND p.pareja2_id != :pareja_lucero
            ORDER BY p.fecha_hora
        """), {
            "tid": TORNEO_ID,
            "pid_excluir": partido_22.id,
            "pareja_lucero": PAREJA_LUCERO_PAEZ
        }).fetchall()
        
        print(f"\n✅ Analizando {len(candidatos)} partidos candidatos...")
        
        intercambios_viables = []
        
        for cand in candidatos:
            cand_fecha_hora = cand.fecha_hora
            cand_dia_semana = cand_fecha_hora.weekday()
            cand_hora_local = cand_fecha_hora.strftime("%H:%M")
            
            cand_p1_rest = parse_restricciones(cand.p1_restricciones)
            cand_p2_rest = parse_restricciones(cand.p2_restricciones)
            
            # Verificar si las parejas del partido a las 22 pueden jugar en el horario del candidato
            p1_puede_cand = puede_jugar_horario(p1_rest, cand_dia_semana, cand_hora_local)
            p2_puede_cand = puede_jugar_horario(p2_rest, cand_dia_semana, cand_hora_local)
            
            # Verificar si Lucero/Paez puede jugar en el horario del candidato
            lp_puede_cand = puede_jugar_horario(lp_rest, cand_dia_semana, cand_hora_local)
            
            # Verificar si las parejas del candidato pueden jugar a las 22
            cand_p1_puede_22 = puede_jugar_horario(cand_p1_rest, dia_semana, hora_local)
            cand_p2_puede_22 = puede_jugar_horario(cand_p2_rest, dia_semana, hora_local)
            
            if p1_puede_cand and p2_puede_cand and lp_puede_cand and cand_p1_puede_22 and cand_p2_puede_22:
                intercambios_viables.append({
                    'partido_id': cand.id,
                    'pareja1': cand.pareja1_nombre,
                    'pareja2': cand.pareja2_nombre,
                    'fecha_hora': cand_fecha_hora,
                    'hora_local': cand_hora_local,
                    'cancha_id': cand.cancha_id
                })
        
        print(f"\n{'=' * 80}")
        print(f"✅ INTERCAMBIOS VIABLES ENCONTRADOS: {len(intercambios_viables)}")
        print(f"{'=' * 80}")
        
        if intercambios_viables:
            print(f"\nPartidos que pueden intercambiar horario con Lucero/Paez (22:00):")
            for i, ic in enumerate(intercambios_viables[:10], 1):
                print(f"\n{i}. Partido #{ic['partido_id']}")
                print(f"   {ic['pareja1']} vs {ic['pareja2']}")
                print(f"   Horario actual: {ic['fecha_hora'].strftime('%Y-%m-%d %H:%M')} - Cancha {ic['cancha_id']}")
                print(f"   → Lucero/Paez iría a: {ic['hora_local']}")
                print(f"   → Este partido iría a: 22:00")
        else:
            print("\n❌ No se encontraron intercambios viables")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
