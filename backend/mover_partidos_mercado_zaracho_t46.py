"""
Mover los 2 partidos restantes de Mercado + Zaracho
Estos solo pueden jugar sábado 00:30 (viernes noche)
"""
import sys, os
from datetime import datetime, timedelta, time
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

# Partidos con Mercado + Zaracho (pareja 1017)
PARTIDOS_MERCADO_ZARACHO = {
    1045: ("Silva + Aguilar", "Mercado + Zaracho", 1011, 1017),
    1046: ("Lucero + Folledo", "Mercado + Zaracho", 1002, 1017),
}

def main():
    print("=" * 80)
    print("MOVIENDO PARTIDOS DE MERCADO + ZARACHO")
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
        
        viernes = torneo.fecha_inicio
        sabado = viernes + timedelta(days=1)
        
        # Horario único disponible para Mercado + Zaracho: sábado 00:30
        horario_especial = datetime.combine(sabado, time(0, 30))
        
        print(f"\n📅 Horario especial para Mercado + Zaracho: {horario_especial}")
        print("   (Sábado 00:30 = viernes noche después de medianoche)")
        
        print("\n" + "=" * 80)
        print("MOVIENDO PARTIDOS")
        print("=" * 80)
        
        movidos = 0
        
        for partido_id, (p1_nombre, p2_nombre, p1_id, p2_id) in PARTIDOS_MERCADO_ZARACHO.items():
            # Obtener info del partido
            partido = conn.execute(text("""
                SELECT id_partido, fecha_hora FROM partidos WHERE id_partido = :pid
            """), {"pid": partido_id}).fetchone()
            
            if not partido:
                print(f"\n⚠️  Partido {partido_id} no encontrado")
                continue
            
            print(f"\n🎾 Partido {partido_id}: {p1_nombre} vs {p2_nombre}")
            print(f"   Horario actual: {partido.fecha_hora}")
            
            # Verificar si hay solapamiento en el horario especial
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
                "fh": horario_especial,
                "p1": p1_id,
                "p2": p2_id
            }).fetchone()[0]
            
            if solapamiento > 0:
                # Intentar 00:40, 00:50, 01:00
                for minutos in [40, 50, 60]:
                    horario_alt = datetime.combine(sabado, time(0, minutos if minutos < 60 else 0)) + (timedelta(hours=1) if minutos == 60 else timedelta())
                    
                    solapamiento_alt = conn.execute(text("""
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
                        "fh": horario_alt,
                        "p1": p1_id,
                        "p2": p2_id
                    }).fetchone()[0]
                    
                    if solapamiento_alt == 0:
                        horario_especial = horario_alt
                        break
            
            # Actualizar partido
            conn.execute(text("""
                UPDATE partidos 
                SET fecha_hora = :fh
                WHERE id_partido = :pid
            """), {"fh": horario_especial, "pid": partido_id})
            
            print(f"   ✅ Movido a: {horario_especial}")
            movidos += 1
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ {movidos}/{len(PARTIDOS_MERCADO_ZARACHO)} PARTIDOS MOVIDOS")
        print("=" * 80)
        
        # Verificación final completa
        print("\n📊 DISTRIBUCIÓN FINAL DE TODOS LOS PARTIDOS:")
        partidos_por_dia = conn.execute(text("""
            SELECT 
                CASE EXTRACT(DOW FROM fecha_hora)
                    WHEN 5 THEN 'Viernes'
                    WHEN 6 THEN 'Sábado'
                    WHEN 0 THEN 'Domingo'
                END as dia,
                CASE 
                    WHEN EXTRACT(DOW FROM fecha_hora) = 6 AND EXTRACT(HOUR FROM fecha_hora) >= 16 THEN 'Tarde (>=16:00)'
                    WHEN EXTRACT(DOW FROM fecha_hora) = 6 AND EXTRACT(HOUR FROM fecha_hora) < 2 THEN 'Madrugada (<02:00)'
                    ELSE 'Normal'
                END as momento,
                COUNT(*) as cantidad
            FROM partidos
            WHERE id_torneo = :tid AND categoria_id = :cid
            GROUP BY EXTRACT(DOW FROM fecha_hora), 
                     CASE 
                        WHEN EXTRACT(DOW FROM fecha_hora) = 6 AND EXTRACT(HOUR FROM fecha_hora) >= 16 THEN 'Tarde (>=16:00)'
                        WHEN EXTRACT(DOW FROM fecha_hora) = 6 AND EXTRACT(HOUR FROM fecha_hora) < 2 THEN 'Madrugada (<02:00)'
                        ELSE 'Normal'
                     END
            ORDER BY EXTRACT(DOW FROM fecha_hora)
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        total_partidos = 0
        for d in partidos_por_dia:
            if d.dia:
                if d.dia == "Domingo":
                    estado = "❌"
                elif d.momento == "Tarde (>=16:00)":
                    estado = "❌"
                elif d.momento == "Madrugada (<02:00)":
                    estado = "⚠️ "
                else:
                    estado = "✅"
                print(f"  {estado} {d.dia} {d.momento}: {d.cantidad} partidos")
                total_partidos += d.cantidad
        
        print(f"\n  TOTAL: {total_partidos} partidos")
        
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
            print(f"  ❌ {len(solapamientos)} solapamientos detectados")
        else:
            print("  ✅ No hay solapamientos")

if __name__ == "__main__":
    main()
