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
        print("DEBUG: ¿Por qué el frontend no lista los partidos?")
        print("=" * 80)
        
        # 1. Verificar que los partidos tienen id_torneo
        print("\n1️⃣ VERIFICAR id_torneo")
        print("─" * 80)
        
        partidos_con_id = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos
            WHERE id_torneo = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        print(f"Partidos con id_torneo = {TORNEO_ID}: {partidos_con_id}")
        
        # 2. Verificar que los partidos tienen categoria_id
        print("\n2️⃣ VERIFICAR categoria_id en partidos")
        print("─" * 80)
        
        partidos_sin_categoria = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos
            WHERE id_torneo = :tid
            AND categoria_id IS NULL
        """), {"tid": TORNEO_ID}).scalar()
        
        print(f"Partidos SIN categoria_id: {partidos_sin_categoria}")
        
        if partidos_sin_categoria > 0:
            print("⚠️  PROBLEMA: Los partidos no tienen categoria_id")
            print("El frontend probablemente filtra por categoría y no encuentra nada")
        
        # 3. Ver estructura de un partido
        print("\n3️⃣ ESTRUCTURA DE UN PARTIDO")
        print("─" * 80)
        
        ejemplo = s.execute(text("""
            SELECT 
                p.id_partido,
                p.id_torneo,
                p.categoria_id,
                p.zona_id,
                tz.nombre as zona_nombre,
                tz.categoria_id as zona_categoria_id,
                tc.nombre as categoria_nombre
            FROM partidos p
            LEFT JOIN torneo_zonas tz ON p.zona_id = tz.id
            LEFT JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE p.id_torneo = :tid
            LIMIT 1
        """), {"tid": TORNEO_ID}).fetchone()
        
        if ejemplo:
            print(f"Partido #{ejemplo[0]}:")
            print(f"  id_torneo: {ejemplo[1]}")
            print(f"  categoria_id (en partido): {ejemplo[2]}")
            print(f"  zona_id: {ejemplo[3]}")
            print(f"  zona_nombre: {ejemplo[4]}")
            print(f"  categoria_id (de la zona): {ejemplo[5]}")
            print(f"  categoria_nombre: {ejemplo[6]}")
            
            if ejemplo[2] is None and ejemplo[5] is not None:
                print("\n⚠️  PROBLEMA DETECTADO:")
                print("Los partidos NO tienen categoria_id en la tabla partidos")
                print("Pero SÍ tienen zona, y la zona tiene categoria_id")
                print("\n💡 SOLUCIÓN:")
                print("Actualizar categoria_id en partidos desde sus zonas")
        
        # 4. Verificar query del endpoint con categoria_id
        print("\n4️⃣ SIMULAR QUERY DEL ENDPOINT")
        print("─" * 80)
        
        # Query sin filtro de categoría
        sin_filtro = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            WHERE p.id_torneo = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        print(f"Sin filtro de categoría: {sin_filtro} partidos")
        
        # Query con filtro de categoría (como hace el frontend)
        categorias = s.execute(text("""
            SELECT id, nombre
            FROM torneo_categorias
            WHERE torneo_id = :tid
        """), {"tid": TORNEO_ID}).fetchall()
        
        for cat in categorias:
            con_filtro = s.execute(text("""
                SELECT COUNT(*)
                FROM partidos p
                WHERE p.id_torneo = :tid
                AND p.categoria_id = :cid
            """), {"tid": TORNEO_ID, "cid": cat[0]}).scalar()
            
            print(f"Con filtro categoría {cat[1]} (ID {cat[0]}): {con_filtro} partidos")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
