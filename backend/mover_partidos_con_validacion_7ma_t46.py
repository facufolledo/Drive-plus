"""
Mover partidos indebidos de 7ma torneo 46 validando restricciones y solapamientos
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

TORNEO_ID = 46

# Partidos indebidos identificados
PARTIDOS_INDEBIDOS = {
    1059: "Brizuela + Moreno vs Millicay + Carrizo",
    1051: "Barros + Cruz vs Diaz + Jofre",
    1065: "Villarrubia + Ibanaz vs Nieto + Olivera",
    1044: "Silva + Aguilar vs Lucero + Folledo",
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
        'monday': 'lunes',
        'tuesday': 'martes',
        'wednesday': 'miercoles',
        'thursday': 'jueves',
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
                return False  # Está en una restricción (NO disponible)
    
    return True

def main():
    print("=" * 80)
    print("MOVIENDO PARTIDOS CON VALIDACIÓN COMPLETA - 7MA TORNEO 46")
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
        
        # Obtener horarios de partidos bien programados
        horarios_validos = conn.execute(text("""
            SELECT DISTINCT fecha_hora
            FROM partidos
            WHERE id_torneo = :tid 
              AND categoria_id = :cid
              AND EXTRACT(DOW FROM fecha_hora) IN (5, 6)
              AND (
                EXTRACT(DOW FROM fecha_hora) = 5
                OR (EXTRACT(DOW FROM fecha_hora) = 6 AND EXTRACT(HOUR FROM fecha_hora) < 16)
              )
            ORDER BY fecha_hora
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        print(f"\n📅 HORARIOS VÁLIDOS DISPONIBLES: {len(horarios_validos)}")
        
        # Procesar cada partido indebido
        print("\n" + "=" * 80)
        print("MOVIENDO PARTIDOS CON VALIDACIÓN")
        print("=" * 80)
        
        movidos = 0
        no_movidos = []
        
        for partido_id, descripcion in PARTIDOS_INDEBIDOS.items():
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
            print(f"   Parejas: {partido.pareja1_id} vs {partido.pareja2_id}")
            
            restr1 = partido.restr1 if partido.restr1 else []
            restr2 = partido.restr2 if partido.restr2 else []
            
            if restr1:
                print(f"   Restricciones P1: {len(restr1)} bloques")
            if restr2:
                print(f"   Restricciones P2: {len(restr2)} bloques")
            
            # Buscar primer horario disponible que cumpla TODAS las condiciones
            nuevo_horario = None
            intentos = 0
            
            for h in horarios_validos:
                intentos += 1
                fecha_hora_test = h.fecha_hora
                
                # 1. Verificar restricciones de ambas parejas
                if not verificar_disponibilidad_pareja(restr1, fecha_hora_test):
                    continue
                
                if not verificar_disponibilidad_pareja(restr2, fecha_hora_test):
                    continue
                
                # 2. Verificar que no haya solapamiento con las mismas parejas
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
            
            if nuevo_horario:
                # Actualizar partido
                conn.execute(text("""
                    UPDATE partidos 
                    SET fecha_hora = :fh
                    WHERE id_partido = :pid
                """), {"fh": nuevo_horario, "pid": partido_id})
                
                print(f"   ✅ Movido a: {nuevo_horario} (intentos: {intentos})")
                movidos += 1
            else:
                print(f"   ❌ No se encontró horario válido (intentos: {intentos})")
                no_movidos.append((partido_id, descripcion))
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ {movidos}/{len(PARTIDOS_INDEBIDOS)} PARTIDOS MOVIDOS")
        print("=" * 80)
        
        if no_movidos:
            print("\n⚠️  PARTIDOS NO MOVIDOS:")
            for pid, desc in no_movidos:
                print(f"  - Partido {pid}: {desc}")
        
        # Verificar resultado final
        print("\n📊 VERIFICACIÓN FINAL:")
        partidos_por_dia = conn.execute(text("""
            SELECT 
                CASE EXTRACT(DOW FROM fecha_hora)
                    WHEN 5 THEN 'Viernes'
                    WHEN 6 THEN 'Sábado'
                    WHEN 0 THEN 'Domingo'
                END as dia,
                CASE 
                    WHEN EXTRACT(DOW FROM fecha_hora) = 6 AND EXTRACT(HOUR FROM fecha_hora) >= 16 THEN 'Tarde'
                    ELSE 'OK'
                END as momento,
                COUNT(*) as cantidad
            FROM partidos
            WHERE id_torneo = :tid AND categoria_id = :cid
            GROUP BY EXTRACT(DOW FROM fecha_hora), 
                     CASE WHEN EXTRACT(DOW FROM fecha_hora) = 6 AND EXTRACT(HOUR FROM fecha_hora) >= 16 THEN 'Tarde' ELSE 'OK' END
            ORDER BY EXTRACT(DOW FROM fecha_hora)
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        for d in partidos_por_dia:
            if d.dia:
                estado = "✅" if d.momento == "OK" and d.dia != "Domingo" else "❌"
                print(f"  {estado} {d.dia} {d.momento}: {d.cantidad} partidos")
        
        # Verificar solapamientos
        print("\n🔍 VERIFICANDO SOLAPAMIENTOS:")
        solapamientos = conn.execute(text("""
            SELECT p1.id_partido, p2.id_partido, p1.fecha_hora,
                   p1.pareja1_id, p1.pareja2_id
            FROM partidos p1
            JOIN partidos p2 ON p1.fecha_hora = p2.fecha_hora 
                AND p1.id_partido < p2.id_partido
                AND (
                    p1.pareja1_id IN (p2.pareja1_id, p2.pareja2_id)
                    OR p1.pareja2_id IN (p2.pareja1_id, p2.pareja2_id)
                )
            WHERE p1.id_torneo = :tid AND p1.categoria_id = :cid
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        if solapamientos:
            print(f"  ❌ {len(solapamientos)} solapamientos detectados:")
            for s in solapamientos:
                print(f"     Partidos {s[0]} y {s[1]} - {s[2]} - Parejas: {s[3]}, {s[4]}")
        else:
            print("  ✅ No hay solapamientos")

if __name__ == "__main__":
    main()
