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
        print("VERIFICAR PARTIDOS PARA FRONTEND - TORNEO 45")
        print("=" * 80)
        
        # Verificar estructura del torneo
        print("\n1️⃣ ESTRUCTURA DEL TORNEO")
        print("─" * 80)
        
        categorias = s.execute(text("""
            SELECT id, nombre
            FROM torneo_categorias
            WHERE torneo_id = :tid
            ORDER BY nombre
        """), {"tid": TORNEO_ID}).fetchall()
        
        print(f"Categorías: {len(categorias)}")
        for cat in categorias:
            print(f"  • {cat[1]} (ID: {cat[0]})")
            
            zonas = s.execute(text("""
                SELECT id, nombre
                FROM torneo_zonas
                WHERE categoria_id = :cid
                ORDER BY nombre
            """), {"cid": cat[0]}).fetchall()
            
            print(f"    Zonas: {len(zonas)}")
            for zona in zonas:
                partidos = s.execute(text("""
                    SELECT COUNT(*)
                    FROM partidos
                    WHERE zona_id = :zid
                """), {"zid": zona[0]}).scalar()
                
                print(f"      • {zona[1]} (ID: {zona[0]}) - {partidos} partidos")
        
        # Verificar partidos sin zona
        print("\n2️⃣ PARTIDOS SIN ZONA")
        print("─" * 80)
        
        partidos_sin_zona = s.execute(text("""
            SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.fecha_hora
            FROM partidos p
            JOIN torneos_parejas tp ON p.pareja1_id = tp.id
            WHERE tp.torneo_id = :tid
            AND p.zona_id IS NULL
        """), {"tid": TORNEO_ID}).fetchall()
        
        if partidos_sin_zona:
            print(f"⚠️  {len(partidos_sin_zona)} partidos sin zona:")
            for p in partidos_sin_zona:
                print(f"  Partido #{p[0]} - Parejas {p[1]} vs {p[2]} - {p[3]}")
        else:
            print("✅ Todos los partidos tienen zona asignada")
        
        # Verificar query del frontend
        print("\n3️⃣ QUERY DEL FRONTEND (simulación)")
        print("─" * 80)
        
        partidos_frontend = s.execute(text("""
            SELECT 
                p.id_partido,
                tz.nombre as zona_nombre,
                tc.nombre as categoria_nombre,
                p.fecha_hora,
                p.estado
            FROM partidos p
            JOIN torneo_zonas tz ON p.zona_id = tz.id
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            WHERE tc.torneo_id = :tid
            ORDER BY tc.nombre, tz.nombre, p.fecha_hora
            LIMIT 10
        """), {"tid": TORNEO_ID}).fetchall()
        
        if partidos_frontend:
            print(f"✅ Frontend puede ver {len(partidos_frontend)} partidos (mostrando primeros 10):")
            for p in partidos_frontend:
                print(f"  Partido #{p[0]} - {p[2]} {p[1]} - {p[3]} - Estado: {p[4]}")
        else:
            print("❌ Frontend NO puede ver partidos")
        
        # Totales
        print("\n4️⃣ TOTALES")
        print("─" * 80)
        
        total_partidos = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp ON p.pareja1_id = tp.id
            WHERE tp.torneo_id = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        total_con_zona = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp ON p.pareja1_id = tp.id
            WHERE tp.torneo_id = :tid
            AND p.zona_id IS NOT NULL
        """), {"tid": TORNEO_ID}).scalar()
        
        print(f"Total partidos: {total_partidos}")
        print(f"Partidos con zona: {total_con_zona}")
        print(f"Partidos sin zona: {total_partidos - total_con_zona}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
