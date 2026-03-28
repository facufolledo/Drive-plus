import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

# Fechas base
FECHA_BASE_JUEVES = datetime(2026, 3, 5)
FECHA_BASE_VIERNES = datetime(2026, 3, 6)
FECHA_BASE_SABADO = datetime(2026, 3, 7)

# IDs de canchas
CANCHAS = {
    1: 89,  # Cancha 1
    2: 90,  # Cancha 2
    3: 91   # Cancha 3
}

# Partidos faltantes para zonas de 2 parejas (solo 1vs2)
PARTIDOS_FALTANTES = {
    '6ta': {
        'H': {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '01:00', 'cancha': 3},
        'I': {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '22:00', 'cancha': 2}
    },
    '4ta': {
        'F': {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '19:00', 'cancha': 2}
    }
}

def obtener_fecha_hora(dia, hora_str):
    """Convertir día y hora a datetime"""
    dias_map = {
        'Jueves': FECHA_BASE_JUEVES,
        'Viernes': FECHA_BASE_VIERNES,
        'Sabado': FECHA_BASE_SABADO
    }
    
    fecha_base = dias_map[dia]
    hora, minuto = map(int, hora_str.split(':'))
    
    # Si es 01:00, es del día siguiente (madrugada)
    if hora == 1:
        fecha_base = fecha_base + timedelta(days=1)
    
    return fecha_base.replace(hour=hora, minute=minuto)

def main():
    s = Session()
    try:
        print("=" * 80)
        print("CREAR PARTIDOS FALTANTES EN ZONAS DE 2 PAREJAS - T45")
        print("=" * 80)
        
        total_creados = 0
        
        for cat_nombre, zonas in PARTIDOS_FALTANTES.items():
            print(f"\n📂 Categoría: {cat_nombre}")
            
            for zona_nombre, partido_data in zonas.items():
                print(f"\n  Zona {zona_nombre}:")
                print(f"  {'─' * 70}")
                
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
                    "zona": f"Zona {zona_nombre}"
                }).fetchone()
                
                if not zona:
                    print(f"  ❌ Zona no encontrada")
                    continue
                
                # Buscar parejas de la zona
                parejas_bd = s.execute(text("""
                    SELECT tp.id
                    FROM torneos_parejas tp
                    JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
                    WHERE tzp.zona_id = :zid
                    ORDER BY tp.id
                """), {"zid": zona.id}).fetchall()
                
                if len(parejas_bd) != 2:
                    print(f"  ⚠️  Zona tiene {len(parejas_bd)} parejas (se esperaban 2)")
                    continue
                
                print(f"  Parejas: {parejas_bd[0][0]} vs {parejas_bd[1][0]}")
                
                # Verificar si ya existe el partido
                partido_existe = s.execute(text("""
                    SELECT COUNT(*)
                    FROM partidos
                    WHERE zona_id = :zid
                    AND pareja1_id = :p1
                    AND pareja2_id = :p2
                """), {
                    "zid": zona.id,
                    "p1": parejas_bd[0][0],
                    "p2": parejas_bd[1][0]
                }).scalar()
                
                if partido_existe > 0:
                    print(f"  ℹ️  Partido ya existe")
                    continue
                
                # Crear partido
                fecha_hora = obtener_fecha_hora(partido_data['dia'], partido_data['hora'])
                cancha_id = CANCHAS[partido_data['cancha']]
                
                s.execute(text("""
                    INSERT INTO partidos (
                        pareja1_id,
                        pareja2_id,
                        zona_id,
                        fecha_hora,
                        fecha,
                        cancha_id,
                        estado,
                        id_creador
                    ) VALUES (
                        :p1,
                        :p2,
                        :zona,
                        :fecha,
                        :fecha_solo,
                        :cancha,
                        'pendiente',
                        1
                    )
                """), {
                    "p1": parejas_bd[0][0],
                    "p2": parejas_bd[1][0],
                    "zona": zona.id,
                    "fecha": fecha_hora,
                    "fecha_solo": fecha_hora.date(),
                    "cancha": cancha_id
                })
                
                total_creados += 1
                print(f"  ✅ Partido creado: {partido_data['dia']} {partido_data['hora']} Cancha {partido_data['cancha']}")
        
        s.commit()
        
        print(f"\n{'=' * 80}")
        print(f"✅ PROCESO COMPLETADO")
        print(f"{'=' * 80}")
        print(f"  Partidos creados: {total_creados}")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
