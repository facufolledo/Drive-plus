import os
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
CANCHAS = {1: 89, 2: 90, 3: 91}

# Parejas faltantes para zonas existentes
PAREJAS_FALTANTES_ZONAS_EXISTENTES = {
    '6ta': {
        'H': {
            'pareja': ['FIGUEROA', 'LUCAS'],
            'partidos': [
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '17:00', 'cancha': 3},
                {'cruce': '3vs1', 'dia': 'Jueves', 'hora': '23:00', 'cancha': 1}
            ]
        },
        'I': {
            'pareja': ['LUCERO', 'NICOLAS', 'PAEZ', 'LUCIANO'],
            'partidos': [
                {'cruce': '2vs3', 'dia': 'Viernes', 'hora': '17:00', 'cancha': 2},
                {'cruce': '3vs1', 'dia': 'Viernes', 'hora': '20:00', 'cancha': 2}
            ]
        }
    },
    '4ta': {
        'F': {
            'pareja': ['AGÜERO', 'ALE', 'LOIS', 'HOGA'],
            'partidos': [
                {'cruce': '2vs3', 'dia': 'Sabado', 'hora': '12:00', 'cancha': 2},
                {'cruce': '3vs1', 'dia': 'Sabado', 'hora': '14:00', 'cancha': 2}
            ]
        }
    }
}

# Zonas nuevas a crear
ZONAS_NUEVAS = {
    '4ta': {
        'H': {
            'parejas': [
                ['AGUIRRE', 'AGUSTIN', 'BARRERA', 'BRAIAN'],
                ['CORONAS', 'ALAN']
            ],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Sabado', 'hora': '12:00', 'cancha': 3}
            ]
        },
        'I': {
            'parejas': [
                ['MAGUI', 'JUAN', 'GARCIA', 'MATEO'],
                ['CONFIRMAR', 'CONFIRMAR']  # Segunda pareja a confirmar según imagen
            ],
            'partidos': [
                {'cruce': '1vs2', 'dia': 'Jueves', 'hora': '17:00', 'cancha': 3}
            ]
        }
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
    
    if hora == 1:
        fecha_base = fecha_base + timedelta(days=1)
    
    return fecha_base.replace(hour=hora, minute=minuto)

def buscar_o_crear_usuario(s, nombre, apellido, categoria):
    """Buscar usuario existente o crear uno nuevo"""
    nombre_usuario = f"{nombre.lower()}.{apellido.lower()}.{categoria}.t45"
    
    # Buscar usuario existente
    usuario = s.execute(text("""
        SELECT id_usuario FROM usuarios WHERE nombre_usuario = :nombre_usuario
    """), {"nombre_usuario": nombre_usuario}).fetchone()
    
    if usuario:
        return usuario[0]
    
    # Crear nuevo usuario
    result = s.execute(text("""
        INSERT INTO usuarios (nombre_usuario, email, password_hash, rating)
        VALUES (:nombre_usuario, :email, :password, 1500)
        RETURNING id_usuario
    """), {
        "nombre_usuario": nombre_usuario,
        "email": f"{nombre_usuario}@temp.com",
        "password": "temp_password_hash"
    })
    
    return result.fetchone()[0]

def inscribir_pareja(s, cat_nombre, zona_id, jugadores):
    """Inscribir una pareja en una zona"""
    # Crear usuarios
    if len(jugadores) == 2:
        # Pareja individual - crear jugador ficticio para j2
        j1_id = buscar_o_crear_usuario(s, jugadores[0], jugadores[1], cat_nombre.lower())
        j2_id = buscar_o_crear_usuario(s, "SIN", "PAREJA", cat_nombre.lower())
    elif len(jugadores) == 4:
        j1_id = buscar_o_crear_usuario(s, jugadores[0], jugadores[1], cat_nombre.lower())
        j2_id = buscar_o_crear_usuario(s, jugadores[2], jugadores[3], cat_nombre.lower())
    else:
        raise ValueError(f"Jugadores inválidos: {jugadores}")
    
    # Crear pareja
    pareja_result = s.execute(text("""
        INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id, pago_estado)
        VALUES (:tid, :j1, :j2, 'pagado')
        RETURNING id
    """), {
        "tid": TORNEO_ID,
        "j1": j1_id,
        "j2": j2_id
    })
    
    pareja_id = pareja_result.fetchone()[0]
    
    # Asignar a zona
    s.execute(text("""
        INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
        VALUES (:zona, :pareja)
    """), {
        "zona": zona_id,
        "pareja": pareja_id
    })
    
    return pareja_id

def crear_partidos(s, zona_id, partidos_data):
    """Crear partidos para una zona"""
    # Obtener parejas de la zona
    parejas = s.execute(text("""
        SELECT tp.id
        FROM torneos_parejas tp
        JOIN torneo_zona_parejas tzp ON tp.id = tzp.pareja_id
        WHERE tzp.zona_id = :zid
        ORDER BY tp.id
    """), {"zid": zona_id}).fetchall()
    
    pareja_map = {i+1: p[0] for i, p in enumerate(parejas)}
    
    partidos_creados = 0
    for partido_data in partidos_data:
        cruce = partido_data['cruce']
        p1_num, p2_num = map(int, cruce.replace('vs', ' ').split())
        
        if p1_num not in pareja_map or p2_num not in pareja_map:
            print(f"      ⚠️  Cruce {cruce}: parejas no encontradas")
            continue
        
        fecha_hora = obtener_fecha_hora(partido_data['dia'], partido_data['hora'])
        cancha_id = CANCHAS[partido_data['cancha']]
        
        s.execute(text("""
            INSERT INTO partidos (
                pareja1_id, pareja2_id, zona_id, fecha_hora, fecha,
                cancha_id, estado, id_creador
            ) VALUES (
                :p1, :p2, :zona, :fecha, :fecha_solo,
                :cancha, 'pendiente', 1
            )
        """), {
            "p1": pareja_map[p1_num],
            "p2": pareja_map[p2_num],
            "zona": zona_id,
            "fecha": fecha_hora,
            "fecha_solo": fecha_hora.date(),
            "cancha": cancha_id
        })
        
        partidos_creados += 1
        print(f"      ✅ {cruce} {partido_data['dia']} {partido_data['hora']} C{partido_data['cancha']}")
    
    return partidos_creados

def main():
    s = Session()
    try:
        print("=" * 80)
        print("COMPLETAR FIXTURE T45 - INSCRIBIR PAREJAS Y CREAR PARTIDOS")
        print("=" * 80)
        
        total_parejas = 0
        total_partidos = 0
        
        # 1. Inscribir parejas faltantes en zonas existentes
        print("\n1️⃣ INSCRIBIR PAREJAS FALTANTES EN ZONAS EXISTENTES")
        print("=" * 80)
        
        for cat_nombre, zonas in PAREJAS_FALTANTES_ZONAS_EXISTENTES.items():
            print(f"\n📂 {cat_nombre}")
            
            for zona_nombre, zona_data in zonas.items():
                print(f"\n  Zona {zona_nombre}:")
                
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
                    print(f"    ❌ Zona no encontrada")
                    continue
                
                # Inscribir pareja
                pareja_id = inscribir_pareja(s, cat_nombre, zona.id, zona_data['pareja'])
                print(f"    ✅ Pareja inscrita: ID {pareja_id}")
                total_parejas += 1
                
                # Crear partidos
                partidos = crear_partidos(s, zona.id, zona_data['partidos'])
                total_partidos += partidos
        
        s.commit()
        
        # 2. Crear zonas nuevas con parejas y partidos
        print(f"\n\n2️⃣ CREAR ZONAS NUEVAS")
        print("=" * 80)
        
        orden_zona = {'H': 8, 'I': 9}
        
        for cat_nombre, zonas in ZONAS_NUEVAS.items():
            print(f"\n📂 {cat_nombre}")
            
            # Obtener categoría
            categoria = s.execute(text("""
                SELECT id FROM torneo_categorias
                WHERE torneo_id = :tid AND nombre = :cat
            """), {"tid": TORNEO_ID, "cat": cat_nombre}).fetchone()
            
            if not categoria:
                print(f"  ❌ Categoría no encontrada")
                continue
            
            for zona_nombre, zona_data in zonas.items():
                print(f"\n  Zona {zona_nombre}:")
                
                # Crear zona
                zona_result = s.execute(text("""
                    INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
                    VALUES (:tid, :cat_id, :nombre, :orden)
                    RETURNING id
                """), {
                    "tid": TORNEO_ID,
                    "cat_id": categoria[0],
                    "nombre": f"Zona {zona_nombre}",
                    "orden": orden_zona[zona_nombre]
                })
                
                zona_id = zona_result.fetchone()[0]
                print(f"    ✅ Zona creada: ID {zona_id}")
                
                # Inscribir parejas
                for jugadores in zona_data['parejas']:
                    pareja_id = inscribir_pareja(s, cat_nombre, zona_id, jugadores)
                    print(f"    ✅ Pareja inscrita: ID {pareja_id}")
                    total_parejas += 1
                
                # Crear partidos
                partidos = crear_partidos(s, zona_id, zona_data['partidos'])
                total_partidos += partidos
        
        s.commit()
        
        print(f"\n{'=' * 80}")
        print("✅ PROCESO COMPLETADO")
        print("=" * 80)
        print(f"  Parejas inscritas: {total_parejas}")
        print(f"  Partidos creados: {total_partidos}")
        
        # Verificar totales
        total_parejas_bd = s.execute(text("""
            SELECT COUNT(*)
            FROM torneos_parejas
            WHERE torneo_id = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        total_partidos_bd = s.execute(text("""
            SELECT COUNT(*)
            FROM partidos p
            JOIN torneos_parejas tp ON p.pareja1_id = tp.id
            WHERE tp.torneo_id = :tid
        """), {"tid": TORNEO_ID}).scalar()
        
        print(f"\n{'=' * 80}")
        print("TOTALES EN BD")
        print("=" * 80)
        print(f"  Total parejas: {total_parejas_bd} (esperado: 68)")
        print(f"  Total partidos: {total_partidos_bd} (esperado: 65)")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
