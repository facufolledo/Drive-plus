"""
Verificar TODOS los partidos de 7ma considerando timezone UTC-3
"""
import sys, os
from datetime import datetime, timedelta
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

def verificar_restriccion(restricciones, fecha_hora_utc):
    """Verifica si un horario viola restricciones (considerando UTC-3)"""
    if not restricciones:
        return True, "Sin restricciones"
    
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
                return False, f"VIOLA: {dia_esp} {hora_str} en rango restringido {hora_inicio}-{hora_fin}"
    
    return True, f"OK: {dia_esp} {hora_str}"

def main():
    print("=" * 80)
    print("VERIFICANDO TODOS LOS PARTIDOS 7MA CON TIMEZONE")
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
        
        # Obtener todos los partidos con restricciones
        partidos = conn.execute(text("""
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
            WHERE p.id_torneo = :tid AND p.categoria_id = :cid
            ORDER BY p.fecha_hora
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        print(f"\n✅ Total partidos: {len(partidos)}\n")
        
        violaciones = []
        
        for p in partidos:
            hora_utc = p.fecha_hora
            hora_local = hora_utc - timedelta(hours=3)
            
            # Verificar restricciones de ambas parejas
            ok1, msg1 = verificar_restriccion(p.restr1, hora_utc)
            ok2, msg2 = verificar_restriccion(p.restr2, hora_utc)
            
            if not ok1 or not ok2:
                violaciones.append(p)
                print(f"❌ PARTIDO {p.id_partido}")
                print(f"   UTC: {hora_utc} → Local: {hora_local}")
                print(f"   P1 ({p.pareja1_id}): {p.j1_u1} + {p.j1_u2}")
                print(f"      {msg1}")
                print(f"   P2 ({p.pareja2_id}): {p.j2_u1} + {p.j2_u2}")
                print(f"      {msg2}")
                print()
        
        if not violaciones:
            print("✅ TODOS LOS PARTIDOS RESPETAN LAS RESTRICCIONES")
        else:
            print("=" * 80)
            print(f"❌ {len(violaciones)} PARTIDOS VIOLAN RESTRICCIONES")
            print("=" * 80)
        
        # Mostrar distribución por día LOCAL
        print("\n📊 DISTRIBUCIÓN POR DÍA (HORA LOCAL ARGENTINA):")
        
        viernes_count = 0
        sabado_temprano = 0
        sabado_tarde = 0
        domingo_count = 0
        
        for p in partidos:
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
        
        print(f"  ✅ Viernes: {viernes_count} partidos")
        print(f"  ✅ Sábado temprano (<16:00): {sabado_temprano} partidos")
        if sabado_tarde > 0:
            print(f"  ❌ Sábado tarde (>=16:00): {sabado_tarde} partidos")
        if domingo_count > 0:
            print(f"  ❌ Domingo: {domingo_count} partidos")

if __name__ == "__main__":
    main()
