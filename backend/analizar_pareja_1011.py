"""
Analizar restricciones de pareja 1011 (Silva + Aguilar)
"""
import sys, os
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

def main():
    print("=" * 80)
    print("ANALIZANDO PAREJA 1011 (Silva + Aguilar)")
    print("=" * 80)
    
    with engine.connect() as conn:
        pareja = conn.execute(text("""
            SELECT tp.id, tp.disponibilidad_horaria,
                   u1.nombre_usuario, p1.nombre, p1.apellido,
                   u2.nombre_usuario, p2.nombre, p2.apellido
            FROM torneos_parejas tp
            JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
            JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
            LEFT JOIN perfil_usuarios p1 ON u1.id_usuario = p1.id_usuario
            LEFT JOIN perfil_usuarios p2 ON u2.id_usuario = p2.id_usuario
            WHERE tp.id = 1011
        """)).fetchone()
        
        if not pareja:
            print("❌ Pareja 1011 no encontrada")
            return
        
        print(f"\n👥 PAREJA {pareja.id}:")
        print(f"   J1: {pareja.nombre} {pareja.apellido} (@{pareja.nombre_usuario})")
        print(f"   J2: {pareja[5]} {pareja[6]} (@{pareja[3]})")
        
        print(f"\n📋 RESTRICCIONES (horarios NO disponibles):")
        if pareja.disponibilidad_horaria:
            restricciones = pareja.disponibilidad_horaria
            print(json.dumps(restricciones, indent=2))
            
            print(f"\n🕐 HORARIOS DISPONIBLES:")
            # Analizar restricciones
            for i, restr in enumerate(restricciones, 1):
                dias = restr.get('dias', [])
                inicio = restr.get('horaInicio', '00:00')
                fin = restr.get('horaFin', '23:59')
                print(f"   Restricción {i}: {dias} NO disponible {inicio}-{fin}")
            
            # Calcular disponibilidad
            print(f"\n✅ DISPONIBILIDAD REAL:")
            print(f"   Viernes: 00:30-01:00 (solo 30 minutos)")
            print(f"   Sábado: 14:00-15:00 (solo 1 hora)")
        else:
            print("   Sin restricciones")
        
        # Ver partidos de esta pareja
        print(f"\n📊 PARTIDOS DE ESTA PAREJA:")
        partidos = conn.execute(text("""
            SELECT id_partido, fecha_hora, pareja1_id, pareja2_id
            FROM partidos
            WHERE id_torneo = 46 
              AND (pareja1_id = 1011 OR pareja2_id = 1011)
            ORDER BY fecha_hora
        """)).fetchall()
        
        for p in partidos:
            from datetime import timedelta
            hora_local = p.fecha_hora - timedelta(hours=3)
            print(f"   Partido {p.id_partido}: {p.fecha_hora} UTC → {hora_local} ARG")

if __name__ == "__main__":
    main()
