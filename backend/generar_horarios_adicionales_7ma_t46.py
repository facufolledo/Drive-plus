"""
Generar horarios adicionales para mover los 4 partidos restantes
Crear slots cada 70 minutos en viernes y sábado temprano
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

# Partidos que no pudieron moverse
PARTIDOS_PENDIENTES = {
    1051: "Barros + Cruz vs Diaz + Jofre",
    1052: "Bedini + Johannesen vs Diaz + Jofre",
    1045: "Silva + Aguilar vs Mercado + Zaracho",
    1046: "Lucero + Folledo vs Mercado + Zaracho",
}

def verificar_disponibilidad_pareja(restricciones, fecha_hora):
    """Verifica si una pareja puede jugar en un horario dado"""
    if not restricciones:
        return True
    
    dia_semana = fecha_hora.strftime('%A').lower()
    dia_map = {
        'friday': 'viernes',
        'saturday': 'sabado',
        'sunday': 'domingo'
    }
    dia_esp = dia_map.get(dia_semana, dia_semana)
    hora_str = fecha_hora.strftime('%H:%M')
    
    for restr in restricciones:
        if dia_esp in restr.get('dias', []):
            hora_inicio = restr.get('horaInicio', '00:00')
            hora_fin = restr.get('horaFin', '23:59')
            
            if hora_inicio <= hora_str <= hora_fin:
                return False
    
    return True

def generar_slots_horarios(fecha_base, hora_inicio, hora_fin, intervalo_min=70):
    """Genera lista de horarios cada X minutos"""
    slots = []
    hora_actual = datetime.combine(fecha_base, hora_inicio)
    hora_limite = datetime.combine(fecha_base, hora_fin)
    
    while hora_actual <= hora_limite:
        slots.append(hora_actual)
        hora_actual += timedelta(minutes=intervalo_min)
    
    return slots

def main():
    print("=" * 80)
    print("GENERANDO HORARIOS ADICIONALES Y MOVIENDO PARTIDOS PENDIENTES")
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
        
        # Obtener fecha inicio del torneo
        torneo = conn.execute(text("""
            SELECT fecha_inicio FROM torneos WHERE id = :tid
        """), {"tid": TORNEO_ID}).fetchone()
        
        viernes = torneo.fecha_inicio
        sabado = viernes + timedelta(days=1)
        
        print(f"\n📅 Viernes: {viernes}")
        print(f"📅 Sábado: {sabado}")
        
        # Generar slots adicionales
        # Viernes: 14:00 - 23:59 cada 70 min
        # Sábado: 08:00 - 15:59 cada 70 min
        slots_viernes = generar_slots_horarios(viernes, time(14, 0), time(23, 59), 70)
        slots_sabado = generar_slots_horarios(sabado, time(8, 0), time(15, 59), 70)
        
        todos_slots = slots_viernes + slots_sabado
        
        print(f"\n📅 SLOTS GENERADOS: {len(todos_slots)}")
        print(f"  Viernes: {len(slots_viernes)} slots")
        print(f"  Sábado: {len(slots_sabado)} slots")
        
        # Procesar cada partido pendiente
        print("\n" + "=" * 80)
        print("MOVIENDO PARTIDOS PENDIENTES")
        print("=" * 80)
        
        movidos = 0
        
        for partido_id, descripcion in PARTIDOS_PENDIENTES.items():
            # Obtener info del partido
            partido = conn.execute(text("""
                SELECT p.id_partido, p.fecha_hora, p.pareja1_id, p.pareja2_id,
                       tp1.disponibilidad_horaria as restr1,
                       tp2.disponibilidad_horaria as restr2
                FROM partidos p
                LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
                WHERE p.id_partido = :pid
            """), {"pid": partido_id}).fetchone()
            
            if not partido:
                print(f"\n⚠️  Partido {partido_id} no encontrado")
                continue
            
            print(f"\n🎾 Partido {partido_id}: {descripcion}")
            print(f"   Horario actual: {partido.fecha_hora}")
            
            restr1 = partido.restr1 if partido.restr1 else []
            restr2 = partido.restr2 if partido.restr2 else []
            
            # Buscar primer horario disponible
            nuevo_horario = None
            
            for slot in todos_slots:
                # 1. Verificar restricciones
                if not verificar_disponibilidad_pareja(restr1, slot):
                    continue
                
                if not verificar_disponibilidad_pareja(restr2, slot):
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
                    "pid": partido_id,
                    "fh": slot,
                    "p1": partido.pareja1_id,
                    "p2": partido.pareja2_id
                }).fetchone()[0]
                
                if solapamiento == 0:
                    nuevo_horario = slot
                    break
            
            if nuevo_horario:
                conn.execute(text("""
                    UPDATE partidos 
                    SET fecha_hora = :fh
                    WHERE id_partido = :pid
                """), {"fh": nuevo_horario, "pid": partido_id})
                
                print(f"   ✅ Movido a: {nuevo_horario}")
                movidos += 1
            else:
                print(f"   ❌ No se encontró horario válido")
                # Mostrar restricciones para debug
                if restr1:
                    print(f"      P1 restricciones: {json.dumps(restr1, indent=6)}")
                if restr2:
                    print(f"      P2 restricciones: {json.dumps(restr2, indent=6)}")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ {movidos}/{len(PARTIDOS_PENDIENTES)} PARTIDOS MOVIDOS")
        print("=" * 80)
        
        # Verificación final
        print("\n📊 DISTRIBUCIÓN FINAL:")
        partidos_por_dia = conn.execute(text("""
            SELECT 
                CASE EXTRACT(DOW FROM fecha_hora)
                    WHEN 5 THEN 'Viernes'
                    WHEN 6 THEN 'Sábado'
                    WHEN 0 THEN 'Domingo'
                END as dia,
                COUNT(*) as cantidad
            FROM partidos
            WHERE id_torneo = :tid AND categoria_id = :cid
            GROUP BY EXTRACT(DOW FROM fecha_hora)
            ORDER BY EXTRACT(DOW FROM fecha_hora)
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        for d in partidos_por_dia:
            if d.dia:
                estado = "✅" if d.dia != "Domingo" else "❌"
                print(f"  {estado} {d.dia}: {d.cantidad} partidos")

if __name__ == "__main__":
    main()
