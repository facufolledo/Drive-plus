"""
Reprogramar partidos de 7ma torneo 46 que están en horarios indebidos
Mover partidos de domingo y sábado tarde a viernes o sábado temprano
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

# IDs de partidos indebidos
PARTIDOS_INDEBIDOS = [
    # Sábado tarde
    1059, 1051, 1065,
    # Domingo
    1044, 1052, 1045, 1046
]

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
                return False  # Está en una restricción
    
    return True

def main():
    print("=" * 80)
    print("REPROGRAMANDO PARTIDOS INDEBIDOS 7MA TORNEO 46")
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
        
        # Obtener horarios disponibles del torneo
        horarios = conn.execute(text("""
            SELECT dia_semana, hora_inicio, hora_fin, intervalo_minutos
            FROM torneo_horarios
            WHERE torneo_id = :tid
            ORDER BY 
                CASE dia_semana 
                    WHEN 'viernes' THEN 1 
                    WHEN 'sabado' THEN 2 
                    WHEN 'domingo' THEN 3 
                END,
                hora_inicio
        """), {"tid": TORNEO_ID}).fetchall()
        
        print(f"\n📅 HORARIOS DEL TORNEO:")
        for h in horarios:
            print(f"  {h.dia_semana}: {h.hora_inicio} - {h.hora_fin} (intervalo: {h.intervalo_minutos}min)")
        
        # Obtener fecha de inicio del torneo
        torneo = conn.execute(text("""
            SELECT fecha_inicio FROM torneos WHERE id = :tid
        """), {"tid": TORNEO_ID}).fetchone()
        
        fecha_inicio = torneo.fecha_inicio
        print(f"\n📅 Fecha inicio torneo: {fecha_inicio}")
        
        # Calcular viernes y sábado
        viernes = fecha_inicio
        sabado = fecha_inicio + timedelta(days=1)
        
        print(f"  Viernes: {viernes}")
        print(f"  Sábado: {sabado}")
        
        # Procesar cada partido indebido
        print("\n" + "=" * 80)
        print("REPROGRAMANDO PARTIDOS")
        print("=" * 80)
        
        for partido_id in PARTIDOS_INDEBIDOS:
            # Obtener info del partido
            partido = conn.execute(text("""
                SELECT p.id_partido, p.fecha_hora, p.cancha_id, p.fase,
                       p.pareja1_id, p.pareja2_id,
                       tp1.disponibilidad_horaria as restr1,
                       tp2.disponibilidad_horaria as restr2
                FROM partidos p
                LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
                WHERE p.id_partido = :pid
            """), {"pid": partido_id}).fetchone()
            
            if not partido:
                print(f"⚠️  Partido {partido_id} no encontrado")
                continue
            
            print(f"\n🎾 Partido {partido_id}")
            print(f"   Horario actual: {partido.fecha_hora}")
            print(f"   Parejas: {partido.pareja1_id} vs {partido.pareja2_id}")
            
            restr1 = partido.restr1 if partido.restr1 else []
            restr2 = partido.restr2 if partido.restr2 else []
            
            # Buscar primer horario disponible (priorizar viernes, luego sábado temprano)
            nuevo_horario = None
            
            # Intentar viernes primero
            for h in horarios:
                if h.dia_semana != 'viernes':
                    continue
                
                hora_inicio = datetime.strptime(h.hora_inicio, '%H:%M').time()
                hora_fin = datetime.strptime(h.hora_fin, '%H:%M').time()
                intervalo = h.intervalo_minutos
                
                hora_actual = hora_inicio
                while hora_actual <= hora_fin:
                    fecha_hora_test = datetime.combine(viernes, hora_actual)
                    
                    # Verificar disponibilidad de ambas parejas
                    if (verificar_disponibilidad_pareja(restr1, fecha_hora_test) and
                        verificar_disponibilidad_pareja(restr2, fecha_hora_test)):
                        
                        # Verificar que no haya solapamiento con otras parejas
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
                            "fh": fecha_hora_test,
                            "p1": partido.pareja1_id,
                            "p2": partido.pareja2_id
                        }).fetchone()[0]
                        
                        if solapamiento == 0:
                            nuevo_horario = fecha_hora_test
                            break
                    
                    # Avanzar al siguiente intervalo
                    minutos_totales = hora_actual.hour * 60 + hora_actual.minute + intervalo
                    hora_actual = datetime.strptime(f"{minutos_totales // 60:02d}:{minutos_totales % 60:02d}", '%H:%M').time()
                
                if nuevo_horario:
                    break
            
            # Si no encontró en viernes, intentar sábado temprano (<16:00)
            if not nuevo_horario:
                for h in horarios:
                    if h.dia_semana != 'sabado':
                        continue
                    
                    hora_inicio = datetime.strptime(h.hora_inicio, '%H:%M').time()
                    hora_fin = datetime.strptime(h.hora_fin, '%H:%M').time()
                    hora_limite = datetime.strptime('16:00', '%H:%M').time()
                    hora_fin = min(hora_fin, hora_limite)
                    intervalo = h.intervalo_minutos
                    
                    hora_actual = hora_inicio
                    while hora_actual <= hora_fin:
                        fecha_hora_test = datetime.combine(sabado, hora_actual)
                        
                        if (verificar_disponibilidad_pareja(restr1, fecha_hora_test) and
                            verificar_disponibilidad_pareja(restr2, fecha_hora_test)):
                            
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
                                "fh": fecha_hora_test,
                                "p1": partido.pareja1_id,
                                "p2": partido.pareja2_id
                            }).fetchone()[0]
                            
                            if solapamiento == 0:
                                nuevo_horario = fecha_hora_test
                                break
                        
                        minutos_totales = hora_actual.hour * 60 + hora_actual.minute + intervalo
                        hora_actual = datetime.strptime(f"{minutos_totales // 60:02d}:{minutos_totales % 60:02d}", '%H:%M').time()
                    
                    if nuevo_horario:
                        break
            
            if nuevo_horario:
                # Actualizar partido
                conn.execute(text("""
                    UPDATE partidos 
                    SET fecha_hora = :fh
                    WHERE id_partido = :pid
                """), {"fh": nuevo_horario, "pid": partido_id})
                
                print(f"   ✅ Movido a: {nuevo_horario}")
            else:
                print(f"   ❌ No se encontró horario disponible")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ REPROGRAMACIÓN COMPLETADA")
        print("=" * 80)

if __name__ == "__main__":
    main()
