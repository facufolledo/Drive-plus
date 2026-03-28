import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def main():
    s = Session()
    try:
        result = s.execute(text("""
            SELECT 
                tz.nombre,
                tz.id as zona_id,
                COUNT(DISTINCT tzp.pareja_id) as parejas,
                COUNT(DISTINCT p.id_partido) as partidos
            FROM torneo_zonas tz
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            LEFT JOIN torneo_zona_parejas tzp ON tzp.zona_id = tz.id
            LEFT JOIN partidos p ON p.zona_id = tz.id
            WHERE tc.torneo_id = 45 AND tc.nombre = '4ta'
            GROUP BY tz.nombre, tz.id
            ORDER BY tz.nombre
        """)).fetchall()
        
        print("Zona       | Parejas | Partidos | Esperado | Estado")
        print("-" * 60)
        
        total_parejas = 0
        total_partidos = 0
        
        for r in result:
            zona, zona_id, parejas, partidos = r
            esperado = (parejas * (parejas - 1)) // 2
            estado = "✅" if partidos == esperado else f"⚠️ (+{partidos - esperado})"
            print(f"{zona:<10} | {parejas:<7} | {partidos:<8} | {esperado:<8} | {estado}")
            total_parejas += parejas
            total_partidos += partidos
            
            # Si hay problema, mostrar parejas
            if partidos != esperado:
                parejas_zona = s.execute(text("""
                    SELECT 
                        tp.id,
                        u1.nombre_usuario as j1,
                        u2.nombre_usuario as j2
                    FROM torneo_zona_parejas tzp
                    JOIN torneos_parejas tp ON tzp.pareja_id = tp.id
                    JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
                    JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
                    WHERE tzp.zona_id = :zid
                """), {"zid": zona_id}).fetchall()
                
                print(f"  Parejas en {zona}:")
                for p in parejas_zona:
                    print(f"    - ID {p[0]}: {p[1]} / {p[2]}")
        
        print("-" * 60)
        print(f"TOTAL: {total_parejas} parejas, {total_partidos} partidos")
        print(f"Esperado: 22 partidos (6 zonas de 3 + 4 zonas de 2)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
