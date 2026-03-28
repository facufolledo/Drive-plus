#!/usr/bin/env python3
"""
Verificar qué parejas hay en las zonas que no generaron todos los partidos
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

# Zonas que tuvieron errores según el output
ZONAS_PROBLEMA = [
    ('6ta', 'Zona H'),
    ('6ta', 'Zona I'),
    ('4ta', 'Zona F'),
    ('4ta', 'Zona H'),
    ('4ta', 'Zona I')
]

def main():
    s = Session()
    try:
        print("=" * 80)
        print("VERIFICAR PAREJAS EN ZONAS INCOMPLETAS")
        print("=" * 80)
        
        for cat_nombre, zona_nombre in ZONAS_PROBLEMA:
            print(f"\n{cat_nombre} - {zona_nombre}:")
            print("-" * 80)
            
            # Buscar zona
            zona = s.execute(text("""
                SELECT tz.id
                FROM torneo_zonas tz
                JOIN torneo_categorias tc ON tz.categoria_id = tc.id
                WHERE tc.torneo_id = :tid
                AND tc.nombre = :cat
                AND tz.nombre = :zona
            """), {
                "tid": TORNEO_ID,
                "cat": cat_nombre,
                "zona": zona_nombre
            }).fetchone()
            
            if not zona:
                print(f"  ❌ Zona no existe")
                continue
            
            # Buscar parejas
            parejas = s.execute(text("""
                SELECT 
                    tp.id,
                    u1.nombre_usuario as j1,
                    u2.nombre_usuario as j2
                FROM torneos_parejas tp
                JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
                JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
                JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
                WHERE tp.torneo_id = :tid
                AND tzp.zona_id = :zid
                ORDER BY tp.id
            """), {
                "tid": TORNEO_ID,
                "zid": zona.id
            }).fetchall()
            
            print(f"  Total parejas: {len(parejas)}")
            for i, p in enumerate(parejas, 1):
                print(f"    {i}. Pareja {p.id}: {p.j1} - {p.j2}")
            
            if len(parejas) < 3:
                print(f"  ⚠️  Faltan {3 - len(parejas)} parejas para completar la zona")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
