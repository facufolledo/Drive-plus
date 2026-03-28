"""
Verificar estructura del torneo 46 - horarios y canchas
"""
import sys, os
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
    print("ESTRUCTURA TORNEO 46")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Info básica del torneo
        torneo = conn.execute(text("""
            SELECT id, nombre, fecha_inicio, fecha_fin
            FROM torneos WHERE id = 46
        """)).fetchone()
        
        if not torneo:
            print("❌ Torneo 46 no encontrado")
            return
        
        print(f"\n📋 TORNEO:")
        print(f"  ID: {torneo.id}")
        print(f"  Nombre: {torneo.nombre}")
        print(f"  Fecha inicio: {torneo.fecha_inicio}")
        print(f"  Fecha fin: {torneo.fecha_fin}")
        
        # Verificar si hay slots
        slots = conn.execute(text("""
            SELECT id, dia_semana, hora_inicio, hora_fin
            FROM torneo_slots
            WHERE torneo_id = 46
            ORDER BY dia_semana, hora_inicio
        """)).fetchall()
        
        if slots:
            print(f"\n📅 SLOTS ({len(slots)}):")
            for s in slots:
                print(f"  {s.dia_semana}: {s.hora_inicio} - {s.hora_fin}")
        else:
            print("\n⚠️  No hay slots definidos")
        
        # Verificar canchas
        canchas = conn.execute(text("""
            SELECT id, nombre FROM torneo_canchas WHERE torneo_id = 46
        """)).fetchall()
        
        if canchas:
            print(f"\n🏟️  CANCHAS ({len(canchas)}):")
            for c in canchas:
                print(f"  ID {c.id}: {c.nombre}")
        else:
            print("\n⚠️  No hay canchas definidas")
        
        # Ver distribución de partidos por día
        print("\n" + "=" * 80)
        print("DISTRIBUCIÓN DE PARTIDOS 7MA")
        print("=" * 80)
        
        cat = conn.execute(text("""
            SELECT id FROM torneo_categorias WHERE torneo_id = 46 AND nombre = '7ma'
        """)).fetchone()
        
        if not cat:
            print("❌ Categoría 7ma no encontrada")
            return
        
        partidos_por_dia = conn.execute(text("""
            SELECT 
                TO_CHAR(fecha_hora, 'Day') as dia,
                DATE(fecha_hora) as fecha,
                COUNT(*) as cantidad
            FROM partidos
            WHERE id_torneo = 46 AND categoria_id = :cid
            GROUP BY DATE(fecha_hora), TO_CHAR(fecha_hora, 'Day')
            ORDER BY DATE(fecha_hora)
        """), {"cid": cat.id}).fetchall()
        
        for d in partidos_por_dia:
            print(f"  {d.dia.strip()}: {d.fecha} - {d.cantidad} partidos")

if __name__ == "__main__":
    main()
