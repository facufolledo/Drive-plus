"""
Arreglar los últimos 3 partidos problemáticos
- 1044: Silva + Aguilar vs Lucero + Folledo
- 1045: Silva + Aguilar vs Mercado + Zaracho  
- 1046: Lucero + Folledo vs Mercado + Zaracho
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
    print("ARREGLANDO ÚLTIMOS 3 PARTIDOS")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Obtener categoria_id
        cat = conn.execute(text("""
            SELECT id FROM torneo_categorias WHERE torneo_id = :tid AND nombre = '7ma'
        """), {"tid": TORNEO_ID}).fetchone()
        
        CATEGORIA_ID = cat.id
        
        # Obtener fecha del torneo
        torneo = conn.execute(text("""
            SELECT fecha_inicio FROM torneos WHERE id = :tid
        """), {"tid": TORNEO_ID}).fetchone()
        
        viernes_local = torneo.fecha_inicio
        sabado_local = viernes_local + timedelta(days=1)
        
        print(f"\n📅 Fechas:")
        print(f"  Viernes local: {viernes_local}")
        print(f"  Sábado local: {sabado_local}")
        
        # PARTIDO 1044: Silva + Aguilar (1011) vs Lucero + Folledo (1002)
        # Silva + Aguilar: solo puede viernes 00:30 o sábado 14:00-15:00
        # Lucero + Folledo: viernes después de 16:00
        # SOLUCIÓN: Sábado 14:00 local = 17:00 UTC
        print(f"\n🎾 PARTIDO 1044:")
        print(f"   Silva + Aguilar: solo viernes 00:30 o sábado 14:00-15:00")
        print(f"   Lucero + Folledo: viernes después de 16:00")
        print(f"   SOLUCIÓN: Sábado 14:00 local")
        
        horario_1044_local = datetime.combine(sabado_local, time(14, 0))
        horario_1044_utc = horario_1044_local + timedelta(hours=3)
        
        conn.execute(text("""
            UPDATE partidos SET fecha_hora = :fh WHERE id_partido = 1044
        """), {"fh": horario_1044_utc})
        print(f"   ✅ Movido a: {horario_1044_utc} UTC → {horario_1044_local} ARG")
        
        # PARTIDO 1045: Silva + Aguilar (1011) vs Mercado + Zaracho (1017)
        # Silva + Aguilar: solo viernes 00:30 o sábado 14:00-15:00
        # Mercado + Zaracho: solo sábado 00:30-01:00
        # SOLUCIÓN: Sábado 00:30 local = 03:30 UTC
        print(f"\n🎾 PARTIDO 1045:")
        print(f"   Silva + Aguilar: solo viernes 00:30 o sábado 14:00-15:00")
        print(f"   Mercado + Zaracho: solo sábado 00:30-01:00")
        print(f"   SOLUCIÓN: Sábado 00:30 local")
        
        horario_1045_local = datetime.combine(sabado_local, time(0, 30))
        horario_1045_utc = horario_1045_local + timedelta(hours=3)
        
        conn.execute(text("""
            UPDATE partidos SET fecha_hora = :fh WHERE id_partido = 1045
        """), {"fh": horario_1045_utc})
        print(f"   ✅ Movido a: {horario_1045_utc} UTC → {horario_1045_local} ARG")
        
        # PARTIDO 1046: Lucero + Folledo (1002) vs Mercado + Zaracho (1017)
        # Lucero + Folledo: viernes después de 16:00
        # Mercado + Zaracho: solo sábado 00:30-01:00
        # SOLUCIÓN: Sábado 00:40 local = 03:40 UTC
        print(f"\n🎾 PARTIDO 1046:")
        print(f"   Lucero + Folledo: viernes después de 16:00")
        print(f"   Mercado + Zaracho: solo sábado 00:30-01:00")
        print(f"   SOLUCIÓN: Sábado 00:40 local")
        
        horario_1046_local = datetime.combine(sabado_local, time(0, 40))
        horario_1046_utc = horario_1046_local + timedelta(hours=3)
        
        conn.execute(text("""
            UPDATE partidos SET fecha_hora = :fh WHERE id_partido = 1046
        """), {"fh": horario_1046_utc})
        print(f"   ✅ Movido a: {horario_1046_utc} UTC → {horario_1046_local} ARG")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ 3 PARTIDOS CORREGIDOS")
        print("=" * 80)
        
        # Verificación final
        print("\n📊 DISTRIBUCIÓN FINAL:")
        partidos = conn.execute(text("""
            SELECT fecha_hora FROM partidos 
            WHERE id_torneo = :tid AND categoria_id = :cid
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchall()
        
        viernes = 0
        sabado_temprano = 0
        sabado_madrugada = 0
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
                    sabado_temprano += 1
                else:
                    sabado_tarde += 1
            elif dia == 'Sunday':
                domingo += 1
        
        print(f"  ✅ Viernes: {viernes} partidos")
        print(f"  ⚠️  Sábado madrugada (00:00-02:00): {sabado_madrugada} partidos")
        print(f"  ✅ Sábado normal (02:00-16:00): {sabado_temprano} partidos")
        if sabado_tarde > 0:
            print(f"  ❌ Sábado tarde (>=16:00): {sabado_tarde} partidos")
        if domingo > 0:
            print(f"  ❌ Domingo: {domingo} partidos")

if __name__ == "__main__":
    main()
