"""
Verificar zona horaria de los partidos
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def verificar_zona_horaria():
    session = Session()
    
    try:
        print("=" * 80)
        print("VERIFICACIÓN DE ZONA HORARIA - PARTIDOS TORNEO 37")
        print("=" * 80)
        
        partidos = session.execute(
            text("""
                SELECT 
                    p.id_partido,
                    p.fecha_hora,
                    p.fecha_hora AT TIME ZONE 'UTC' as fecha_hora_utc,
                    p.fecha_hora AT TIME ZONE 'America/Argentina/Buenos_Aires' as fecha_hora_arg,
                    tc.nombre as cancha
                FROM partidos p
                LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
                WHERE p.id_torneo = 37
                ORDER BY p.fecha_hora
            """)
        ).fetchall()
        
        if not partidos:
            print("\n⚠️  No hay partidos")
            return
        
        print(f"\n📊 PARTIDOS ({len(partidos)}):")
        print("=" * 80)
        
        for p in partidos:
            print(f"\n🎾 Partido #{p[0]} - {p[4]}")
            print(f"   fecha_hora (DB):          {p[1]}")
            print(f"   fecha_hora AT TZ 'UTC':   {p[2]}")
            print(f"   fecha_hora AT TZ 'ARG':   {p[3]}")
            
            # Calcular diferencia
            if p[1] and p[3]:
                diff = (p[1].hour * 60 + p[1].minute) - (p[3].hour * 60 + p[3].minute)
                print(f"   Diferencia: {diff} minutos")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verificar_zona_horaria()
