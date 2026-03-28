#!/usr/bin/env python3
"""
Comparar fixture actual vs fixture deseado de las imágenes
Generar plan de migración completo
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

# Fixture deseado según imágenes (solo algunos ejemplos clave para verificar)
FIXTURE_DESEADO = {
    '6ta': {
        'I': {
            'parejas': [
                'JEREMIAS SALAZAR - CARRIZO JEREMIAS',
                'MATIAS ROSA - MIGUEL ESTRADA', 
                'LUCERO NICLAS - LUCIANO PAEZ'
            ],
            'partidos': [
                {'cruce': '1VS2', 'dia': 'JUEVES', 'hora': '22:00', 'cancha': 2},
                {'cruce': '2VS3', 'dia': 'VIERNES', 'hora': '17:00', 'cancha': 2},
                {'cruce': '3VS1', 'dia': 'JUEVES', 'hora': '19:00', 'cancha': 2}
            ]
        }
    },
    '4ta': {
        'C': {
            'parejas': [
                'FARRAM BASTIAN - MALDONADO ALEXIS',
                'DIAZ MATEO - SOSA BAUTI',
                'BRIZUELA ALVARO - CHUMBITA AGUSTIN'
            ],
            'partidos': [
                {'cruce': '1VS2', 'dia': 'JUEVES', 'hora': '16:00', 'cancha': 3},
                {'cruce': '2VS3', 'dia': 'VIERNES', 'hora': '17:00', 'cancha': 1},
                {'cruce': '3VS1', 'dia': 'VIERNES', 'hora': '22:00', 'cancha': 1}
            ]
        }
    },
    '8va': {
        'D': {
            'parejas': [
                'BRIZUELA MARTIN - CEBALLO SANTIAGO',
                'CORTEZ AGUSTIN - AGUILAR AGUSTIN',
                'LUNA LEONARDO - BORIS NIETO'
            ],
            'partidos': [
                {'cruce': '1VS2', 'dia': 'JUEVES', 'hora': '22:00', 'cancha': 1},
                {'cruce': '2VS3', 'dia': 'VIERNES', 'hora': '01:00', 'cancha': 2},
                {'cruce': '3VS1', 'dia': 'SABADO', 'hora': '13:00', 'cancha': 2}
            ]
        }
    }
}

def normalizar_nombre(nombre):
    """Normalizar nombre para comparación"""
    return nombre.upper().strip().replace('  ', ' ')

def main():
    s = Session()
    try:
        print("=" * 80)
        print("COMPARACIÓN FIXTURE ACTUAL VS DESEADO")
        print("=" * 80)
        
        # Verificar zonas clave
        for cat_nombre, zonas in FIXTURE_DESEADO.items():
            print(f"\n{'=' * 80}")
            print(f"CATEGORÍA: {cat_nombre}")
            print(f"{'=' * 80}")
            
            for zona_nombre, zona_data in zonas.items():
                print(f"\n  Zona {zona_nombre}:")
                print(f"  {'-' * 76}")
                
                # Buscar zona actual
                zona_actual = s.execute(text("""
                    SELECT tz.id, tz.nombre
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
                
                if not zona_actual:
                    print(f"    ❌ Zona {zona_nombre} NO EXISTE en {cat_nombre}")
                    continue
                
                print(f"    ✅ Zona encontrada (ID={zona_actual.id})")
                
                # Verificar parejas
                print(f"\n    Parejas deseadas:")
                for i, pareja_nombre in enumerate(zona_data['parejas'], 1):
                    pareja_actual = s.execute(text("""
                        SELECT tp.id, tp.nombre_pareja
                        FROM torneos_parejas tp
                        JOIN torneo_categorias tc ON tp.categoria_id = tc.id
                        WHERE tp.torneo_id = :tid
                        AND tc.nombre = :cat
                        AND tp.zona_id = :zid
                        AND UPPER(tp.nombre_pareja) LIKE :nombre
                    """), {
                        "tid": TORNEO_ID,
                        "cat": cat_nombre,
                        "zid": zona_actual.id,
                        "nombre": f"%{normalizar_nombre(pareja_nombre)}%"
                    }).fetchone()
                    
                    if pareja_actual:
                        print(f"      {i}. ✅ {pareja_nombre} (ID={pareja_actual.id})")
                    else:
                        print(f"      {i}. ❌ {pareja_nombre} NO ENCONTRADA")
                
                # Verificar partidos
                print(f"\n    Partidos deseados:")
                for partido_deseado in zona_data['partidos']:
                    dia_map = {'JUEVES': 4, 'VIERNES': 5, 'SABADO': 6, 'SÁBADO': 6, 'DOMINGO': 0}
                    dow = dia_map.get(partido_deseado['dia'])
                    hora = int(partido_deseado['hora'].split(':')[0])
                    
                    partido_actual = s.execute(text("""
                        SELECT 
                            p.id_partido,
                            p.fecha_hora,
                            p.cancha_id,
                            tp1.nombre_pareja as p1,
                            tp2.nombre_pareja as p2
                        FROM partidos p
                        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
                        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
                        WHERE p.zona_id = :zid
                        AND EXTRACT(DOW FROM p.fecha_hora) = :dow
                        AND EXTRACT(HOUR FROM p.fecha_hora) = :hora
                        AND p.cancha_id = :cancha
                    """), {
                        "zid": zona_actual.id,
                        "dow": dow,
                        "hora": hora,
                        "cancha": partido_deseado['cancha']
                    }).fetchone()
                    
                    cruce = partido_deseado['cruce']
                    dia = partido_deseado['dia']
                    hora_str = partido_deseado['hora']
                    cancha = partido_deseado['cancha']
                    
                    if partido_actual:
                        print(f"      ✅ {cruce} {dia} {hora_str} C{cancha}: {partido_actual.p1} vs {partido_actual.p2}")
                    else:
                        print(f"      ❌ {cruce} {dia} {hora_str} C{cancha}: NO ENCONTRADO")
        
        print(f"\n{'=' * 80}")
        print("RESUMEN:")
        print(f"{'=' * 80}")
        print("\nEste es un cambio MASIVO que requiere:")
        print("  1. Crear/actualizar zonas")
        print("  2. Crear jugadores nuevos que no existen")
        print("  3. Crear/actualizar parejas")
        print("  4. Reprogramar todos los partidos")
        print("\n⚠️  RECOMENDACIÓN: Hacer backup antes de proceder")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
