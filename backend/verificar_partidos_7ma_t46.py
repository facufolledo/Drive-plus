"""
Verificar partidos de 7ma torneo 46 - identificar horarios indebidos
"""
import sys, os
from datetime import datetime
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

def main():
    print("=" * 80)
    print("VERIFICANDO PARTIDOS 7MA TORNEO 46")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Obtener categoria_id
        cat = conn.execute(text("""
            SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '7ma'
        """)).fetchone()
        
        if not cat:
            print("❌ ERROR: Categoría 7ma no encontrada")
            return
        
        CATEGORIA_ID = cat.id
        
        # Obtener todos los partidos
        partidos = conn.execute(text("""
            SELECT p.id_partido, p.fecha_hora, p.cancha_id, p.fase,
                   tp1.id as pareja1_id, u1.nombre_usuario as j1_u1, u2.nombre_usuario as j1_u2,
                   tp2.id as pareja2_id, u3.nombre_usuario as j2_u1, u4.nombre_usuario as j2_u2
            FROM partidos p
            LEFT JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            LEFT JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            LEFT JOIN usuarios u1 ON tp1.jugador1_id = u1.id_usuario
            LEFT JOIN usuarios u2 ON tp1.jugador2_id = u2.id_usuario
            LEFT JOIN usuarios u3 ON tp2.jugador1_id = u3.id_usuario
            LEFT JOIN usuarios u4 ON tp2.jugador2_id = u4.id_usuario
            WHERE p.id_torneo = 46 AND p.categoria_id = :cid
            ORDER BY p.fecha_hora, p.cancha_id
        """), {"cid": CATEGORIA_ID}).fetchall()
        
        if not partidos:
            print("❌ No se encontraron partidos de 7ma en torneo 46")
            return
        
        print(f"\n✅ Total partidos: {len(partidos)}\n")
        
        # Clasificar partidos
        viernes = []
        sabado_temprano = []
        sabado_tarde = []
        domingo = []
        sin_fecha = []
        
        for p in partidos:
            if not p.fecha_hora:
                sin_fecha.append(p)
                continue
            
            fecha = p.fecha_hora
            dia_semana = fecha.strftime('%A')
            hora = fecha.hour
            
            if dia_semana == 'Friday':
                viernes.append(p)
            elif dia_semana == 'Saturday':
                if hora < 16:
                    sabado_temprano.append(p)
                else:
                    sabado_tarde.append(p)
            elif dia_semana == 'Sunday':
                domingo.append(p)
            else:
                sin_fecha.append(p)
        
        # Mostrar resumen
        print("📊 RESUMEN POR DÍA/HORARIO:")
        print(f"  ✅ Viernes: {len(viernes)} partidos")
        print(f"  ✅ Sábado temprano (<16:00): {len(sabado_temprano)} partidos")
        print(f"  ⚠️  Sábado tarde (>=16:00): {len(sabado_tarde)} partidos - INDEBIDO")
        print(f"  ❌ Domingo: {len(domingo)} partidos - INDEBIDO")
        print(f"  ⚠️  Sin fecha: {len(sin_fecha)} partidos")
        
        # Mostrar partidos indebidos
        if sabado_tarde:
            print("\n" + "=" * 80)
            print("⚠️  PARTIDOS SÁBADO TARDE (>=16:00) - DEBEN MOVERSE")
            print("=" * 80)
            for p in sabado_tarde:
                fecha_str = p.fecha_hora.strftime('%Y-%m-%d %H:%M')
                fase = p.fase or "zona"
                print(f"\n🎾 Partido {p.id_partido} - {fase.upper()} - Cancha {p.cancha_id}")
                print(f"   📅 {fecha_str}")
                print(f"   P1 ({p.pareja1_id}): {p.j1_u1} + {p.j1_u2}")
                print(f"   P2 ({p.pareja2_id}): {p.j2_u1} + {p.j2_u2}")
        
        if domingo:
            print("\n" + "=" * 80)
            print("❌ PARTIDOS DOMINGO - DEBEN MOVERSE")
            print("=" * 80)
            for p in domingo:
                fecha_str = p.fecha_hora.strftime('%Y-%m-%d %H:%M')
                fase = p.fase or "zona"
                print(f"\n🎾 Partido {p.id_partido} - {fase.upper()} - Cancha {p.cancha_id}")
                print(f"   📅 {fecha_str}")
                print(f"   P1 ({p.pareja1_id}): {p.j1_u1} + {p.j1_u2}")
                print(f"   P2 ({p.pareja2_id}): {p.j2_u1} + {p.j2_u2}")
        
        # Contar partidos de zona vs playoffs
        zona_count = sum(1 for p in partidos if not p.fase or p.fase == 'zona')
        playoff_count = len(partidos) - zona_count
        
        print("\n" + "=" * 80)
        print("📊 PARTIDOS POR FASE:")
        print(f"  Zona: {zona_count}")
        print(f"  Playoffs: {playoff_count}")
        print("=" * 80)

if __name__ == "__main__":
    main()
