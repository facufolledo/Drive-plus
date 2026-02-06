"""
Script para inscribir parejas de 5ta en el torneo 37 con sus restricciones horarias
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def inscribir_parejas_5ta():
    """Inscribe las 8 parejas de 5ta en el torneo 37 con sus restricciones"""
    session = Session()
    
    try:
        print("=" * 80)
        print("INSCRIBIR PAREJAS DE 5TA EN TORNEO 37")
        print("=" * 80)
        
        # Verificar que el torneo existe
        torneo = session.execute(
            text("SELECT id, nombre FROM torneos WHERE id = 37")
        ).fetchone()
        
        if not torneo:
            print("❌ El torneo 37 no existe")
            return
        
        print(f"\n✅ Torneo encontrado: {torneo[1]}")
        
        # Obtener la categoría 5ta masculino del torneo 37
        categoria = session.execute(
            text("""
                SELECT id 
                FROM torneo_categorias
                WHERE torneo_id = 37 
                AND nombre = '5ta' 
                AND genero = 'masculino'
            """)
        ).fetchone()
        
        if not categoria:
            print("❌ No se encontró la categoría 5ta masculino en el torneo 37")
            return
        
        categoria_id = categoria[0]
        print(f"✅ Categoría 5ta encontrada (ID: {categoria_id})")
        
        # Parejas a inscribir
        parejas = [
            {
                "nombre": "Chumbita/Martinez",
                "jugador1": {"nombre": "Agustín", "apellido": "Chumbita", "username": "chumbita_agustin"},
                "jugador2": {"nombre": "Lucas", "apellido": "Martinez", "username": "martinez_lucas"},
                "restricciones": [
                    {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
                    {"dias": ["viernes"], "horaInicio": "19:00", "horaFin": "22:30"}
                ]
            },
            {
                "nombre": "Córdoba/Aballay",
                "jugador1": {"nombre": "Tiago", "apellido": "Córdoba", "username": "cordoba_tiago"},
                "jugador2": {"nombre": "Marcelo", "apellido": "Aballay", "username": "aballay_marcelo"},
                "restricciones": [
                    {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "14:00"}
                ]
            },
            {
                "nombre": "Speziale/Zárate",
                "jugador1": {"nombre": "Tomas", "apellido": "Speziale", "username": "speziale_tomas"},
                "jugador2": {"nombre": "Valentín", "apellido": "Zárate", "username": "zarate_valentin"},
                "restricciones": []
            },
            {
                "nombre": "Wamba/Oliva",
                "jugador1": {"nombre": "Bautista", "apellido": "Wamba", "username": "wamba_bautista"},
                "jugador2": {"nombre": "Bautista", "apellido": "Oliva", "username": "oliva_bautista"},
                "restricciones": [
                    {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}
                ]
            },
            {
                "nombre": "Calderón/Villegas",
                "jugador1": {"nombre": "Juan", "apellido": "Calderón", "username": "calderon_juan"},
                "jugador2_real": "ignaciovillegas",  # Usuario real de la app
                "restricciones": []
            },
            {
                "nombre": "Vallejos/Medina",
                "jugador1": {"nombre": "Enzo", "apellido": "Vallejos", "username": "vallejos_enzo"},
                "jugador2": {"nombre": "Juan", "apellido": "Medina", "username": "medina_juan"},
                "restricciones": []
            },
            {
                "nombre": "Merlo/Fernández",
                "jugador1": {"nombre": "Emiliano", "apellido": "Merlo", "username": "merlo_emiliano"},
                "jugador2": {"nombre": "Gabriel", "apellido": "Fernández", "username": "fernandez_gabriel"},
                "restricciones": [
                    {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:30"},
                    {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "16:00"}
                ]
            },
            {
                "nombre": "Ruarte/Romero",
                "jugador1_real": "leandroruarte",  # Usuario real de la app
                "jugador2_real": "gastonromero",   # Usuario real de la app
                "restricciones": [
                    {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}
                ]
            }
        ]
        
        parejas_creadas = 0
        
        for pareja_data in parejas:
            print(f"\n{'='*60}")
            print(f"Procesando: {pareja_data['nombre']}")
            print(f"{'='*60}")
            
            # Manejar jugador 1 (puede ser real o nuevo)
            if 'jugador1_real' in pareja_data:
                # Buscar usuario real por nombre_usuario
                jugador1 = session.execute(
                    text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :username"),
                    {"username": pareja_data['jugador1_real']}
                ).fetchone()
                
                if jugador1:
                    jugador1_id = jugador1[0]
                    print(f"✅ Jugador 1 (real): {pareja_data['jugador1_real']} (ID: {jugador1_id})")
                else:
                    print(f"❌ Jugador 1 real no encontrado: {pareja_data['jugador1_real']}")
                    continue
            else:
                # Crear o buscar jugador 1
                j1 = pareja_data['jugador1']
                jugador1 = session.execute(
                    text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :username"),
                    {"username": j1['username']}
                ).fetchone()
                
                if jugador1:
                    jugador1_id = jugador1[0]
                    print(f"✅ Jugador 1 encontrado: {j1['nombre']} {j1['apellido']} (ID: {jugador1_id})")
                else:
                    result = session.execute(
                        text("""
                            INSERT INTO usuarios (nombre, apellido, email, nombre_usuario, rating, partidos_jugados)
                            VALUES (:nombre, :apellido, :email, :username, 1000, 0)
                            RETURNING id_usuario
                        """),
                        {
                            "nombre": j1['nombre'],
                            "apellido": j1['apellido'],
                            "email": f"{j1['username']}@driveplus.com",
                            "username": j1['username']
                        }
                    )
                    jugador1_id = result.fetchone()[0]
                    print(f"✅ Jugador 1 creado: {j1['nombre']} {j1['apellido']} (ID: {jugador1_id})")
            
            # Manejar jugador 2 (puede ser real o nuevo)
            if 'jugador2_real' in pareja_data:
                # Buscar usuario real por nombre_usuario
                jugador2 = session.execute(
                    text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :username"),
                    {"username": pareja_data['jugador2_real']}
                ).fetchone()
                
                if jugador2:
                    jugador2_id = jugador2[0]
                    print(f"✅ Jugador 2 (real): {pareja_data['jugador2_real']} (ID: {jugador2_id})")
                else:
                    print(f"❌ Jugador 2 real no encontrado: {pareja_data['jugador2_real']}")
                    continue
            else:
                # Crear o buscar jugador 2
                j2 = pareja_data['jugador2']
                jugador2 = session.execute(
                    text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :username"),
                    {"username": j2['username']}
                ).fetchone()
                
                if jugador2:
                    jugador2_id = jugador2[0]
                    print(f"✅ Jugador 2 encontrado: {j2['nombre']} {j2['apellido']} (ID: {jugador2_id})")
                else:
                    result = session.execute(
                        text("""
                            INSERT INTO usuarios (nombre, apellido, email, nombre_usuario, rating, partidos_jugados)
                            VALUES (:nombre, :apellido, :email, :username, 1000, 0)
                            RETURNING id_usuario
                        """),
                        {
                            "nombre": j2['nombre'],
                            "apellido": j2['apellido'],
                            "email": f"{j2['username']}@driveplus.com",
                            "username": j2['username']
                        }
                    )
                    jugador2_id = result.fetchone()[0]
                    print(f"✅ Jugador 2 creado: {j2['nombre']} {j2['apellido']} (ID: {jugador2_id})")
            
            # Verificar si la pareja ya existe
            pareja_existente = session.execute(
                text("""
                    SELECT id FROM parejas_torneo 
                    WHERE torneo_id = :torneo_id 
                    AND ((jugador1_id = :j1 AND jugador2_id = :j2) 
                         OR (jugador1_id = :j2 AND jugador2_id = :j1))
                """),
                {"torneo_id": 37, "j1": jugador1_id, "j2": jugador2_id}
            ).fetchone()
            
            if pareja_existente:
                print(f"⚠️  Pareja ya existe, saltando...")
                continue
            
            # Crear pareja
            restricciones_json = json.dumps(pareja_data['restricciones']) if pareja_data['restricciones'] else None
            
            result = session.execute(
                text("""
                    INSERT INTO parejas_torneo (
                        torneo_id, jugador1_id, jugador2_id, 
                        nombre_pareja, categoria_id, estado_pago,
                        restricciones_horarias
                    ) VALUES (:torneo_id, :j1, :j2, :nombre, :categoria_id, 'confirmado', :restricciones)
                    RETURNING id
                """),
                {
                    "torneo_id": 37,
                    "j1": jugador1_id,
                    "j2": jugador2_id,
                    "nombre": pareja_data['nombre'],
                    "categoria_id": categoria_id,
                    "restricciones": restricciones_json
                }
            )
            
            pareja_id = result.fetchone()[0]
            parejas_creadas += 1
            
            print(f"✅ Pareja creada: {pareja_data['nombre']} (ID: {pareja_id})")
            if pareja_data['restricciones']:
                print(f"   📅 Restricciones: {len(pareja_data['restricciones'])} configuradas")
                for rest in pareja_data['restricciones']:
                    print(f"      - {', '.join(rest['dias'])}: {rest['horaInicio']}-{rest['horaFin']}")
            else:
                print(f"   ✅ Sin restricciones horarias")
        
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ RESUMEN")
        print(f"{'='*60}")
        print(f"Parejas creadas: {parejas_creadas}")
        print(f"Total parejas en 5ta: {len(parejas)}")
        
        # Verificar total de parejas por categoría
        result = session.execute(
            text("""
                SELECT tc.nombre, COUNT(*) 
                FROM parejas_torneo pt
                JOIN torneo_categorias tc ON pt.categoria_id = tc.id
                WHERE pt.torneo_id = 37
                GROUP BY tc.nombre
                ORDER BY tc.nombre
            """)
        )
        
        print(f"\n📊 Parejas por categoría en torneo 37:")
        for nombre_cat, count in result:
            print(f"   {nombre_cat}: {count} parejas")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    inscribir_parejas_5ta()
