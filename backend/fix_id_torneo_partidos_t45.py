import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

def main():
    s = Session()
    try:
        print("=" * 80)
        print("ACTUALIZAR id_torneo EN PARTIDOS - TORNEO 45")
        print("=" * 80)
        
        # Actualizar todos los partidos del torneo 45
        result = s.execute(text("""
            UPDATE partidos
            SET id_torneo = :tid
            WHERE id_partido IN (
                SELECT p.id_partido
                FROM partidos p
                JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                WHERE tp1.torneo_id = :tid
                AND p.id_torneo IS NULL
            )
        """), {"tid": TORNEO_ID})
        
        s.commit()
        
        print(f"\n✅ Actualizados {result.rowcount} partidos con id_torneo = {TORNEO_ID}")
        
        # Verificar
        total_con_id = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            WHERE tp1.torneo_id = :tid
            AND p.id_torneo = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        print(f"✅ Verificación: {total_con_id} partidos ahora tienen id_torneo = {TORNEO_ID}")
        
        # Mostrar algunos ejemplos
        ejemplos = s.execute(text("""
            SELECT 
                p.id_partido,
                p.id_torneo,
                tz.nombre as zona_nombre,
                tc.nombre as categoria_nombre
            FROM partidos p
            JOIN torneo_zonas tz ON p.zona_id = tz.id
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE p.id_torneo = :tid
            ORDER BY tc.nombre, tz.nombre
            LIMIT 5
        """), {"tid": TORNEO_ID}).fetchall()
        
        print("\n📋 Ejemplos de partidos actualizados:")
        print("─" * 80)
        for row in ejemplos:
            print(f"  Partido #{row[0]} - id_torneo: {row[1]} - {row[3]} {row[2]}")
        
        print("\n🎉 ¡Listo! Ahora el frontend debería mostrar los 65 partidos.")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
