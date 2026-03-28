"""
Verificar partido 1044 considerando zona horaria
BD está en UTC, Argentina es UTC-3
"""
import sys, os
from datetime import datetime
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

def main():
    print("=" * 80)
    print("VERIFICANDO PARTIDO 1044 - ZONA HORARIA")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Obtener info del partido 1044
        partido = conn.execute(text("""
            SELECT p.id_partido, p.fecha_hora, p.pareja1_id, p.pareja2_id,
                   u1.nombre_usuario as j1_u1, u2.nombre_usuario as j1_u2,
                   u3.nombre_usuario as j2_u1, u4.nombre_usuario as j2_u2,
                   tp1.disponibilidad_horaria as restr1,
                   tp2.disponibilidad_horaria as restr2
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            JOIN usuarios u1 ON tp1.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp1.jugador2_id = u2.id_usuario
            JOIN usuarios u3 ON tp2.jugador1_id = u3.id_usuario
            JOIN usuarios u4 ON tp2.jugador2_id = u4.id_usuario
            WHERE p.id_partido = 1044
        """)).fetchone()
        
        if not partido:
            print("❌ Partido 1044 no encontrado")
            return
        
        print(f"\n🎾 PARTIDO {partido.id_partido}")
        print(f"   Pareja 1 (ID {partido.pareja1_id}): {partido.j1_u1} + {partido.j1_u2}")
        print(f"   Pareja 2 (ID {partido.pareja2_id}): {partido.j2_u1} + {partido.j2_u2}")
        print(f"\n📅 HORARIO EN BD (UTC):")
        print(f"   {partido.fecha_hora}")
        
        # Convertir a hora local Argentina (UTC-3)
        hora_utc = partido.fecha_hora
        # La BD ya devuelve con timezone UTC
        hora_argentina = hora_utc.replace(tzinfo=None)  # Remover timezone para mostrar
        
        print(f"\n🕐 HORARIO EN ARGENTINA (UTC-3):")
        print(f"   {hora_argentina} - 3 horas = {hora_argentina.hour - 3}:00")
        print(f"   Hora local real: {hora_argentina.hour - 3}:00")
        
        print(f"\n📋 RESTRICCIONES PAREJA 1 ({partido.pareja1_id}):")
        if partido.restr1:
            print(json.dumps(partido.restr1, indent=2))
        else:
            print("   Sin restricciones")
        
        print(f"\n📋 RESTRICCIONES PAREJA 2 ({partido.pareja2_id}):")
        if partido.restr2:
            print(json.dumps(partido.restr2, indent=2))
        else:
            print("   Sin restricciones")
        
        # Verificar si el horario actual viola restricciones
        print(f"\n🔍 ANÁLISIS:")
        hora_local_str = f"{hora_argentina.hour - 3:02d}:00"
        print(f"   Hora local del partido: {hora_local_str}")
        
        # Pareja 2 (Lucero + Folledo) - ID 1002
        if partido.pareja2_id == 1002:
            print(f"\n   Pareja Lucero + Folledo:")
            if partido.restr2:
                for i, restr in enumerate(partido.restr2, 1):
                    print(f"   Restricción {i}: {restr.get('dias')} {restr.get('horaInicio')}-{restr.get('horaFin')}")
                    if 'viernes' in restr.get('dias', []):
                        if restr.get('horaInicio') <= hora_local_str <= restr.get('horaFin'):
                            print(f"      ❌ VIOLA RESTRICCIÓN: {hora_local_str} está en rango NO disponible")
                        else:
                            print(f"      ✅ OK: {hora_local_str} NO está en rango restringido")
            else:
                print("   ✅ Sin restricciones")

if __name__ == "__main__":
    main()
