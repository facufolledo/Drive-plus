"""
Mover partidos indebidos de 7ma torneo 46 a horarios válidos
Estrategia: Usar horarios de partidos ya programados correctamente
"""
import sys, os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine, text

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
    # Sábado tarde
    1059: "Brizuela + Moreno vs Millicay + Carrizo",
    1051: "Barros + Cruz vs Diaz + Jofre",
    1065: "Villarrubia + Ibanaz vs Nieto + Olivera",
    # Domingo
    1044: "Silva + Aguilar vs Lucero + Folledo",
    1052: "Bedini + Johannesen vs Diaz + Jofre",
    1045: "Silva + Aguilar vs Mercado + Zaracho",
    1046: "Lucero + Folledo vs Mercado + Zaracho",
}

def main():
    print("=" * 80)
    print("MOVIENDO PARTIDOS INDEBIDOS 7MA TORNEO 46")
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
        
        # Obtener horarios de partidos bien programados (viernes y sábado temprano)
        horarios_validos = conn.execute(text("""
            SELECT DISTINCT fecha_hora
            FROM partidos
            WHERE id_torneo = :tid 
              AND categoria_id = :cid
              AND EXTRACT(DOW FROM fecha_hora) IN (5, 6)  -- Viernes=5, Sábado=6
              AND (
                EXTRACT(DOW FROM fecha_hora) = 5  -- Viernes: cualquier hora
                OR (EXTRACT(DOW FROM fecha_hora) = 6 AND EXTRACT(HOUR FROM fecha_hora) < 16)  -- Sábado antes de 16:00
              )
            ORDER BY fecha_hora
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        print(f"\n📅 HORARIOS VÁLIDOS DISPONIBLES ({len(horarios_validos)}):")
        for h in horarios_validos[:10]:  # Mostrar primeros 10
            print(f"  {h.fecha_hora}")
        
        # Procesar cada partido indebido
        print("\n" + "=" * 80)
        print("MOVIENDO PARTIDOS")
        print("=" * 80)
        
        movidos = 0
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
            
            # Buscar primer horario disponible
            nuevo_horario = None
            for h in horarios_validos:
                # Verificar que no haya solapamiento con las mismas parejas
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
                    "fh": h.fecha_hora,
                    "p1": partido.pareja1_id,
                    "p2": partido.pareja2_id
                }).fetchone()[0]
                
                if solapamiento == 0:
                    nuevo_horario = h.fecha_hora
                    break
            
            if nuevo_horario:
                # Actualizar partido
                conn.execute(text("""
                    UPDATE partidos 
                    SET fecha_hora = :fh
                    WHERE id_partido = :pid
                """), {"fh": nuevo_horario, "pid": partido_id})
                
                print(f"   ✅ Movido a: {nuevo_horario}")
                movidos += 1
            else:
                print(f"   ❌ No se encontró horario disponible")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ {movidos}/{len(PARTIDOS_INDEBIDOS)} PARTIDOS MOVIDOS")
        print("=" * 80)
        
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

if __name__ == "__main__":
    main()
