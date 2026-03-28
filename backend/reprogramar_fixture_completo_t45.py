#!/usr/bin/env python3
"""
Reprogramar fixture completo T45
1. Eliminar todos los partidos actuales
2. Crear partidos según datos proporcionados
"""
import sys, os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45

# Fechas base del torneo (05-08 marzo 2026)
FECHA_BASE_JUEVES = datetime(2026, 3, 5)
FECHA_BASE_VIERNES = datetime(2026, 3, 6)
FECHA_BASE_SABADO = datetime(2026, 3, 7)
FECHA_BASE_DOMINGO = datetime(2026, 3, 8)

# IDs de canchas
CANCHAS = {1: 89, 2: 90, 3: 91}

# Fixture completo
FIXTURE = {
    '6ta': {
        'A': {
            'parejas': ['VEGA MAXI - MARTIN FACUNDO', 'ROMERO FRANCISCO - ROMERO FERNANDO', 'CEJAS TOMAS - REDES TOMAS'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '22:00', 'cancha': 2},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '18:00', 'cancha': 3},
                {'cruce': '3vs1', 'dia': 'Viernes', 'hora': '23:59', 'cancha': 3}
            ]
        },
        'B': {
            'parejas': ['ORTIZ - SUAREZ', 'SANCHEZ MARTIN - ARREBOLA PUMA', 'SANTILLAN KKE - PAREDES FABIO'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '23:00', 'cancha': 2},
                {'cruce': '2vs3', 'dia': 'Jueves', 'hora': '01:00', 'cancha': 2},
                {'cruce': '3vs1', 'dia': 'Viernes', 'hora': '23:00', 'cancha': 2}
            ]
        },
        'C': {
            'parejas': ['ONTIVERO SAUL - ONTIVERO ISAIAS', 'LLABANTE FEDERICO - CORDOBA SANTIAGO', 'LOBOS JAVIER - SANTANDER MARIO'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '20:00', 'cancha': 2},
                {'cruce': '2vs3', 'dia': 'Jueves', 'hora': '21:00', 'cancha': 3},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '18:00', 'cancha': 3}
            ]
        },
        'D': {
            'parejas': ['NIETO AXEL - NIETO STEFY', 'CEBALLO LAZARO - PAMELIN JORGE', 'OLIVA BAUTI - LEYES FRANCO'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '21:00', 'cancha': 3},
                {'cruce': '2vs3', 'dia': 'Jueves', 'hora': '21:00', 'cancha': 2},
                {'cruce': '3vs1', 'dia': 'Viernes', 'hora': '23:59', 'cancha': 1}
            ]
        },
        'E': {
            'parejas': ['GURGONE CRISTIAN - PALACIO BENJAMIN', 'CORDERO FERNANDO - PEREZ CRISTIAN JR', 'NIS JUAN - FUENTES AGUSTIN'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '20:00', 'cancha': 1},
                {'cruce': '2vs3', 'dia': 'Jueves', 'hora': '19:00', 'cancha': 2},
                {'cruce': '3vs1', 'dia': 'Viernes', 'hora': '23:59', 'cancha': 2}
            ]
        },
        'F': {
            'parejas': ['FERREYRA - BUSTOS', 'CARRIZO MATIAS - JUAREZ LUCAS', 'BAZAN ISAIAS - RODRIGUEZ VALENTINO'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '01:00', 'cancha': 1},
                {'cruce': '2vs3', 'dia': 'Jueves', 'hora': '23:59', 'cancha': 3},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '22:00', 'cancha': 3}
            ]
        },
        'G': {
            'parejas': ['TEJADA RODRIGO - CORZO NICOLAS', 'STIPANICIS YOYO - FUENTES GERE', 'MOLINA ALVARO - MOLINA ALEJO'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '21:00', 'cancha': 1},
                {'cruce': '2vs3', 'dia': 'Jueves', 'hora': '19:00', 'cancha': 1},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '23:59', 'cancha': 1}
            ]
        },
        'H': {
            'parejas': ['RADOSALDOVICH', 'BISET DIEGO - OCAMPO CRISTIAN', 'FIGUEROA LUCAS'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '01:00', 'cancha': 3},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '17:00', 'cancha': 3},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '23:00', 'cancha': 1}
            ]
        },
        'I': {
            'parejas': ['JEREMIAS SALAZAR - CARRIZO JEREMIAS', 'MATIAS ROSA - MIGUEL ESTRADA', 'LUCERO NICOLAS - LUCIANO PAEZ'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '22:00', 'cancha': 2},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '17:00', 'cancha': 2},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '18:00', 'cancha': 2}
            ]
        }
    },
    '4ta': {
        'A': {
            'parejas': ['MILLICAY - TELLO', 'MATIA OLIVERA - JOFRÉ RAMIRO', 'SILVA SERGIO - RODRIGUEZ LUIS'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '15:00', 'cancha': 2},
                {'cruce': '2vs3', 'dia': 'Jueves', 'hora': '01:00', 'cancha': 3},
                {'cruce': '3vs1', 'dia': 'Sabado', 'hora': '16:00', 'cancha': 2}
            ]
        },
        'B': {
            'parejas': ['MERLO - MERLO', 'DEL FRANCO THIAGO - RIVERO JOAQUIN', 'MONTIVERO JUAN FELIPE - JUAN CRUZ'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '15:00', 'cancha': 2},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '18:00', 'cancha': 2},
                {'cruce': '3vs1', 'dia': 'Sabado', 'hora': '11:00', 'cancha': 2}
            ]
        },
        'C': {
            'parejas': ['FARRAN BASTIAN - MALDONADO ALEXIS', 'DIAZ MATEO - SOSA BAUTI', 'BRIZUELA ALVARO - CHUMBITA AGUSTIN'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '16:00', 'cancha': 3},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '17:00', 'cancha': 1},
                {'cruce': '3vs1', 'dia': 'Viernes', 'hora': '22:00', 'cancha': 1}
            ]
        },
        'D': {
            'parejas': ['FIGUEROA - GOMEZ', 'ARREBOLA JERE - BURGONE', 'VILLEGAS NACHO - GAITAN MATIAS'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '21:00', 'cancha': 1},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '18:00', 'cancha': 1},
                {'cruce': '3vs1', 'dia': 'Sabado', 'hora': '11:00', 'cancha': 3}
            ]
        },
        'E': {
            'parejas': ['COPPEDE', 'VERGARA JOAQUIN - FUENTES RICARDO', 'LIGORRIA - BRIZUELA'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '21:00', 'cancha': 2},
                {'cruce': '2vs3', 'dia': 'Sabado', 'hora': '11:00', 'cancha': 1},
                {'cruce': '3vs1', 'dia': 'Sabado', 'hora': '15:00', 'cancha': 2}
            ]
        },
        'F': {
            'parejas': ['NIETO AXEL - GOMEZ MATEO', 'ELIZONDO GERONIMO - CHAVEZ DANIEL', 'AGÜERO ALE - LOIS HOGA'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '19:00', 'cancha': 2},
                {'cruce': '2vs3', 'dia': 'Sabado', 'hora': '12:00', 'cancha': 2},
                {'cruce': '3vs1', 'dia': 'Sabado', 'hora': '14:00', 'cancha': 2}
            ]
        },
        'G': {
            'parejas': ['BESTANI SEBASTIAN - GAVIO CARLOS', 'HERRERA NICOLAS - ORELLANO KEVIN'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Sabado', 'hora': '14:00', 'cancha': 3}
            ]
        },
        'H': {
            'parejas': ['AGUIRRE AGUSTIN - BRAIAN BARRERA', 'ALAN CORONAS'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Sabado', 'hora': '12:00', 'cancha': 3}
            ]
        },
        'I': {
            'parejas': ['CONFIRMAR', 'JUAN MAGUI - MATEO GARCIA'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '17:00', 'cancha': 3}
            ]
        }
    },
    '8va': {
        'A': {
            'parejas': ['ALFARO AXEL - VELAZQUE JUAN', 'VILLANUEVA IGNACIO - FERNANDEZ FACUNDO', 'ALMADA LUCAS - MEDINA JORGE'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Viernes', 'hora': '22:00', 'cancha': 3},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '15:00', 'cancha': 3},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '15:00', 'cancha': 1}
            ]
        },
        'B': {
            'parejas': ['ALFARO BENJA - MANRIQUE FEDERICO', 'OLIVERA LUCAS - GREGORI LUCAS', 'BARRO MAXIMILIANO - BARROS RODRIGO'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '20:00', 'cancha': 3},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '20:00', 'cancha': 3},
                {'cruce': '3vs1', 'dia': 'Viernes', 'hora': '23:00', 'cancha': 3}
            ]
        },
        'C': {
            'parejas': ['COLINA JEREMIAS - COLINA FRANCO', 'BRITOS MAXI - SALAS NANO', 'TOLEDO LEANDRO - TRAMONTIN MATIAS'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '20:00', 'cancha': 2},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '23:00', 'cancha': 1},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '23:00', 'cancha': 3}
            ]
        },
        'D': {
            'parejas': ['BRIZUELA MARTIN - CEBALLO SANTIAGO', 'CORTEZ AGUSTIN - AGUILAR AGUSTIN', 'LUNA LEONARDO - BORIS NIETO'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '22:00', 'cancha': 1},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '01:00', 'cancha': 2},
                {'cruce': '3vs1', 'dia': 'Sabado', 'hora': '13:00', 'cancha': 2}
            ]
        },
        'E': {
            'parejas': ['CALDERON ARIEL - VERA JERE', 'CARDENAS TOBIAS - ROJAS AGUSTIN', 'DIOGENES MIRANDA - DIAMANTE BAUTISTA'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '20:00', 'cancha': 1},
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '19:00', 'cancha': 3},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '16:00', 'cancha': 3}
            ]
        },
        'F': {
            'parejas': ['ZARACHO - MERCADO', 'CORTEZ AGUSTIN - AGUILAR AGUSTIN'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Sabado', 'hora': '10:00', 'cancha': 2}
            ]
        },
        'G': {
            'parejas': ['GONZALEZ JEREMIAS - IMANOL MORALES', 'FUENTES MARTIN - VILLAGRAN JULIAN'],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '23:59', 'cancha': 1}
            ]
        }
    }
}

def normalizar_nombre(nombre):
    """Normalizar nombre para búsqueda"""
    return nombre.upper().strip().replace('  ', ' ')

def obtener_fecha_hora(dia, hora_str):
    """Convertir día y hora a datetime"""
    dias_map = {
        'Jueves': FECHA_BASE_JUEVES,
        'Viernes': FECHA_BASE_VIERNES,
        'Sabado': FECHA_BASE_SABADO,
        'Sábado': FECHA_BASE_SABADO,
        'Domingo': FECHA_BASE_DOMINGO
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
        print("REPROGRAMACIÓN COMPLETA FIXTURE T45")
        print("=" * 80)
        
        # 1. Eliminar todos los partidos actuales
        print("\n1️⃣ Eliminando partidos actuales...")
        result = s.execute(text("""
            DELETE FROM partidos
            WHERE id_partido IN (
                SELECT p.id_partido
                FROM partidos p
                JOIN torneos_parejas tp ON p.pareja1_id = tp.id
                WHERE tp.torneo_id = :tid
            )
        """), {"tid": TORNEO_ID})
        
        print(f"   ✅ {result.rowcount} partidos eliminados")
        s.commit()
        
        # 2. Crear partidos nuevos
        print("\n2️⃣ Creando partidos nuevos...")
        
        total_creados = 0
        total_errores = 0
        
        for cat_nombre, zonas in FIXTURE.items():
            print(f"\n  📂 Categoría: {cat_nombre}")
            
            for zona_nombre, zona_data in zonas.items():
                print(f"    Zona {zona_nombre}:")
                
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
                    print(f"      ❌ Zona no encontrada")
                    continue
                
                # Buscar parejas de la zona
                parejas_bd = s.execute(text("""
                    SELECT tp.id
                    FROM torneos_parejas tp
                    JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
                    WHERE tp.torneo_id = :tid
                    AND tzp.zona_id = :zid
                    ORDER BY tp.id
                """), {
                    "tid": TORNEO_ID,
                    "zid": zona.id
                }).fetchall()
                
                if len(parejas_bd) < 2:
                    print(f"      ⚠️  Solo {len(parejas_bd)} parejas en zona")
                    continue
                
                # Mapear parejas (1, 2, 3)
                pareja_map = {i+1: p.id for i, p in enumerate(parejas_bd)}
                
                # Crear partidos
                for partido_data in zona_data['partidos']:
                    cruce = partido_data['cruce']
                    p1_num, p2_num = map(int, cruce.replace('vs', ' ').split())
                    
                    if p1_num not in pareja_map or p2_num not in pareja_map:
                        print(f"      ❌ Cruce {cruce}: parejas no encontradas")
                        total_errores += 1
                        continue
                    
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
                        "p1": pareja_map[p1_num],
                        "p2": pareja_map[p2_num],
                        "zona": zona.id,
                        "fecha": fecha_hora,
                        "fecha_solo": fecha_hora.date(),
                        "cancha": cancha_id
                    })
                    
                    total_creados += 1
                    print(f"      ✅ {cruce} {partido_data['dia']} {partido_data['hora']} C{partido_data['cancha']}")
        
        s.commit()
        
        print(f"\n{'=' * 80}")
        print(f"✅ REPROGRAMACIÓN COMPLETADA")
        print(f"{'=' * 80}")
        print(f"  Partidos creados: {total_creados}")
        print(f"  Errores: {total_errores}")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
