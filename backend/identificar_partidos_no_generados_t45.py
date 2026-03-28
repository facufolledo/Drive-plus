import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

# Fixture esperado según las imágenes
FIXTURE_ESPERADO = {
    '6ta': {
        'H': {
            'parejas': 3,
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '01:00'},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '17:00'},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '23:00'}
            ]
        },
        'I': {
            'parejas': 3,
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '22:00'},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '17:00'},
                {'cruce': '3vs1', 'dia': 'Viernes', 'hora': '20:00'}
            ]
        }
    },
    '4ta': {
        'F': {
            'parejas': 3,
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '19:00'},
                {'cruce': '2vs3', 'dia': 'Sabado', 'hora': '12:00'},
                {'cruce': '3vs1', 'dia': 'Sabado', 'hora': '14:00'}
            ]
        }
    }
}

def main():
    s = Session()
    try:
        print("=" * 80)
        print("IDENTIFICAR PARTIDOS NO GENERADOS - T45")
        print("=" * 80)
        
        for cat_nombre, zonas in FIXTURE_ESPERADO.items():
            print(f"\n📂 Categoría: {cat_nombre}")
            
            for zona_nombre, zona_data in zonas.items():
                print(f"\n  Zona {zona_nombre}:")
                print(f"  {'─' * 70}")
                
                # Buscar zona
                zona = s.execute(text("""
                    SELECT tz.id, tz.nombre
                    FROM torneo_zonas tz
                    JOIN torneo_categorias tc ON tz.categoria_id = tc.id
                    WHERE tc.torneo_id = :tid
                    AND tc.nombre = :cat
                    AND tz.nombre = :zona
                """), {
                    "tid": TORNEO_ID,
                    "cat": cat_nombre,
                    "zona": f"Zona {zona_nombre}"
                }).fetchone()
                
                if not zona:
                    print(f"  ❌ Zona no existe en BD")
                    continue
                
                # Contar parejas en la zona
                parejas = s.execute(text("""
                    SELECT COUNT(*)
                    FROM torneo_zona_parejas tzp
                    WHERE tzp.zona_id = :zid
                """), {"zid": zona.id}).scalar()
                
                print(f"  Parejas esperadas: {zona_data['parejas']}")
                print(f"  Parejas en BD: {parejas}")
                
                if parejas < zona_data['parejas']:
                    print(f"  ⚠️  FALTAN {zona_data['parejas'] - parejas} PAREJAS")
                    
                    # Listar parejas existentes
                    parejas_bd = s.execute(text("""
                        SELECT tp.id
                        FROM torneos_parejas tp
                        JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
                        WHERE tzp.zona_id = :zid
                        ORDER BY tp.id
                    """), {"zid": zona.id}).fetchall()
                    
                    print(f"\n  Parejas existentes:")
                    for i, p in enumerate(parejas_bd, 1):
                        print(f"    {i}. Pareja ID: {p[0]}")
                
                # Verificar partidos
                print(f"\n  Partidos esperados: {len(zona_data['partidos'])}")
                
                partidos_bd = s.execute(text("""
                    SELECT COUNT(*)
                    FROM partidos p
                    WHERE p.zona_id = :zid
                """), {"zid": zona.id}).scalar()
                
                print(f"  Partidos en BD: {partidos_bd}")
                
                if partidos_bd < len(zona_data['partidos']):
                    print(f"\n  ❌ FALTAN {len(zona_data['partidos']) - partidos_bd} PARTIDOS:")
                    
                    for partido in zona_data['partidos']:
                        print(f"    • {partido['cruce']} - {partido['dia']} {partido['hora']}")
                    
                    print(f"\n  🔍 RAZÓN: Solo hay {parejas} parejas, se necesitan {zona_data['parejas']}")
                    print(f"     Los cruces 2vs3 y 3vs1 no se pueden generar sin la pareja #3")
        
        print(f"\n{'=' * 80}")
        print("RESUMEN")
        print("=" * 80)
        print("\n6 partidos NO generados por falta de parejas:")
        print("\n6ta Zona H (falta 1 pareja):")
        print("  • 2vs3 - Viernes 17:00")
        print("  • 3vs1 - Jueves 23:00")
        print("\n6ta Zona I (falta 1 pareja):")
        print("  • 2vs3 - Viernes 17:00")
        print("  • 3vs1 - Viernes 20:00")
        print("\n4ta Zona F (falta 1 pareja):")
        print("  • 2vs3 - Sabado 12:00")
        print("  • 3vs1 - Sabado 14:00")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
