"""
Debug de horarios del torneo 37 y partidos generados
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def debug_horarios():
    session = Session()
    
    try:
        print("=" * 80)
        print("DEBUG: HORARIOS TORNEO 37")
        print("=" * 80)
        
        # 1. Ver horarios configurados del torneo
        torneo = session.execute(
            text("SELECT id, nombre, fecha_inicio, fecha_fin, horarios_disponibles FROM torneos WHERE id = 37")
        ).fetchone()
        
        if torneo:
            print(f"\n📋 TORNEO: {torneo[1]}")
            print(f"   Fecha inicio: {torneo[2]}")
            print(f"   Fecha fin: {torneo[3]}")
            print(f"\n⏰ HORARIOS CONFIGURADOS:")
            print(f"   Tipo: {type(torneo[4])}")
            print(json.dumps(torneo[4], indent=2))
        
        # 2. Ver partidos generados
        print(f"\n\n{'=' * 80}")
        print("PARTIDOS GENERADOS:")
        print("=" * 80)
        
        partidos = session.execute(
            text("""
                SELECT 
                    p.id_partido,
                    p.fecha_hora,
                    tc.nombre as cancha,
                    tcat.nombre as categoria,
                    u1.nombre_usuario as j1_p1,
                    u2.nombre_usuario as j2_p1,
                    u3.nombre_usuario as j1_p2,
                    u4.nombre_usuario as j2_p2
                FROM partidos p
                JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
                JOIN usuarios u1 ON tp1.jugador1_id = u1.id_usuario
                JOIN usuarios u2 ON tp1.jugador2_id = u2.id_usuario
                JOIN usuarios u3 ON tp2.jugador1_id = u3.id_usuario
                JOIN usuarios u4 ON tp2.jugador2_id = u4.id_usuario
                LEFT JOIN torneo_canchas tc ON p.cancha_id = tc.id
                LEFT JOIN torneo_categorias tcat ON p.categoria_id = tcat.id
                WHERE p.id_torneo = 37
                ORDER BY p.fecha_hora
            """)
        ).fetchall()
        
        if not partidos:
            print("\n⚠️  No hay partidos generados")
        else:
            for p in partidos:
                fecha_hora = p[1]
                dia_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'][fecha_hora.weekday()]
                
                print(f"\n🎾 Partido #{p[0]} - {p[3]}")
                print(f"   {p[4]}/{p[5]} vs {p[6]}/{p[7]}")
                print(f"   📅 {fecha_hora.strftime('%Y-%m-%d %A %H:%M')} ({dia_semana})")
                print(f"   🏟️  {p[2]}")
        
        # 3. Ver canchas activas
        print(f"\n\n{'=' * 80}")
        print("CANCHAS ACTIVAS:")
        print("=" * 80)
        
        canchas = session.execute(
            text("SELECT id, nombre, activa FROM torneo_canchas WHERE torneo_id = 37")
        ).fetchall()
        
        for c in canchas:
            estado = "✅ ACTIVA" if c[2] else "❌ INACTIVA"
            print(f"   • Cancha {c[0]}: {c[1]} - {estado}")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_horarios()
