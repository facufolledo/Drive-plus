"""
Mover partido 1045 a viernes 00:30 (único horario compatible)
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
    print("MOVIENDO PARTIDO 1045 A VIERNES 00:30")
    print("=" * 80)
    
    with engine.connect() as conn:
        torneo = conn.execute(text("""
            SELECT fecha_inicio FROM torneos WHERE id = :tid
        """), {"tid": TORNEO_ID}).fetchone()
        
        viernes_local = torneo.fecha_inicio
        
        # Viernes 00:30 local = 03:30 UTC
        horario_local = datetime.combine(viernes_local, time(0, 30))
        horario_utc = horario_local + timedelta(hours=3)
        
        print(f"\n🎾 PARTIDO 1045: Silva + Aguilar vs Mercado + Zaracho")
        print(f"   Silva + Aguilar: viernes 00:30-01:00 ✅")
        print(f"   Mercado + Zaracho: sábado 00:30-01:00 ❌")
        print(f"   NOTA: No hay horario compatible, usando viernes 00:30")
        print(f"   (Mercado + Zaracho tendrá que hacer excepción)")
        
        conn.execute(text("""
            UPDATE partidos SET fecha_hora = :fh WHERE id_partido = 1045
        """), {"fh": horario_utc})
        
        print(f"\n   ✅ Movido a: {horario_utc} UTC → {horario_local} ARG")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ CORRECCIÓN COMPLETADA")
        print("=" * 80)

if __name__ == "__main__":
    main()
