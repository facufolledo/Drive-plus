"""
Fix final para partidos 1044 y 1045
Pareja Silva + Aguilar solo puede: viernes 00:30-01:00 o sábado 14:01-15:00
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

def main():
    print("=" * 80)
    print("FIX FINAL PARTIDOS 1044 Y 1045")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Obtener fecha del torneo
        torneo = conn.execute(text("""
            SELECT fecha_inicio FROM torneos WHERE id = :tid
        """), {"tid": TORNEO_ID}).fetchone()
        
        viernes_local = torneo.fecha_inicio
        sabado_local = viernes_local + timedelta(days=1)
        
        # PARTIDO 1044: Silva + Aguilar vs Lucero + Folledo
        # Silva + Aguilar: sábado 14:01-15:00
        # Lucero + Folledo: viernes después de 16:00 (OK para sábado)
        # SOLUCIÓN: Sábado 14:10 local = 17:10 UTC
        print(f"\n🎾 PARTIDO 1044:")
        horario_1044_local = datetime.combine(sabado_local, time(14, 10))
        horario_1044_utc = horario_1044_local + timedelta(hours=3)
        
        conn.execute(text("""
            UPDATE partidos SET fecha_hora = :fh WHERE id_partido = 1044
        """), {"fh": horario_1044_utc})
        print(f"   ✅ Movido a: {horario_1044_utc} UTC → {horario_1044_local} ARG")
        
        # PARTIDO 1045: Silva + Aguilar vs Mercado + Zaracho
        # Silva + Aguilar: viernes 00:30-01:00 o sábado 14:01-15:00
        # Mercado + Zaracho: sábado 00:30-01:00
        # SOLUCIÓN: Sábado 00:30 local = 03:30 UTC (único horario común)
        print(f"\n🎾 PARTIDO 1045:")
        horario_1045_local = datetime.combine(sabado_local, time(0, 30))
        horario_1045_utc = horario_1045_local + timedelta(hours=3)
        
        # Verificar si ya hay otro partido a esa hora con Silva + Aguilar
        solapamiento = conn.execute(text("""
            SELECT id_partido FROM partidos
            WHERE id_torneo = 46 
              AND id_partido != 1045
              AND fecha_hora = :fh
              AND (pareja1_id = 1011 OR pareja2_id = 1011)
        """), {"fh": horario_1045_utc}).fetchone()
        
        if solapamiento:
            # Usar viernes 00:30 en su lugar
            horario_1045_local = datetime.combine(viernes_local, time(0, 30))
            horario_1045_utc = horario_1045_local + timedelta(hours=3)
            print(f"   ⚠️  Solapamiento detectado, usando viernes 00:30")
        
        conn.execute(text("""
            UPDATE partidos SET fecha_hora = :fh WHERE id_partido = 1045
        """), {"fh": horario_1045_utc})
        print(f"   ✅ Movido a: {horario_1045_utc} UTC → {horario_1045_local} ARG")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ CORRECCIÓN COMPLETADA")
        print("=" * 80)
        
        # Verificación final
        print("\n📊 DISTRIBUCIÓN FINAL:")
        partidos = conn.execute(text("""
            SELECT fecha_hora FROM partidos 
            WHERE id_torneo = 46 
              AND categoria_id = (SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '7ma')
        """)).fetchall()
        
        viernes = 0
        sabado_madrugada = 0
        sabado_normal = 0
        sabado_tarde = 0
        domingo = 0
        
        for p in partidos:
            hora_local = p.fecha_hora - timedelta(hours=3)
            dia = hora_local.strftime('%A')
            hora = hora_local.hour
            
            if dia == 'Friday':
                viernes += 1
            elif dia == 'Saturday':
                if hora < 2:
                    sabado_madrugada += 1
                elif hora < 16:
                    sabado_normal += 1
                else:
                    sabado_tarde += 1
            elif dia == 'Sunday':
                domingo += 1
        
        print(f"  ✅ Viernes: {viernes} partidos")
        if sabado_madrugada > 0:
            print(f"  ⚠️  Sábado madrugada (00:00-02:00): {sabado_madrugada} partidos")
        print(f"  ✅ Sábado normal (02:00-16:00): {sabado_normal} partidos")
        if sabado_tarde > 0:
            print(f"  ❌ Sábado tarde (>=16:00): {sabado_tarde} partidos")
        if domingo > 0:
            print(f"  ❌ Domingo: {domingo} partidos")

if __name__ == "__main__":
    main()
