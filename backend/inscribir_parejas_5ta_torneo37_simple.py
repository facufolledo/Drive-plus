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
        
        # Verificar torneo
        torneo = session.execute(
            text("SELECT id, nombre FROM torneos WHERE id = 37")
        ).fetchone()
        
        if not torneo:
            print("❌ El torneo 37 no existe")
            return
        
        print(f"\n✅ Torneo encontrado: {torneo[1]}")
        
        # Obtener categoría 5ta
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
            print("❌ No se encontró la categoría 5ta masculino")
            return
        
        categoria_id = categoria[0]
        print(f"✅ Categoría 5ta encontrada (ID: {categoria_id})")
        
        # Buscar IDs de jugadores por username
        def buscar_jugador(username):
            result = session.execute(
                text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :username"),
                {"username": username}
            ).fetchone()
            return result[0] if result else None
        
        # Definir parejas con sus restricciones
        # Formato: (jugador1_id, jugador2_id, restricciones)
        parejas_data = [
            # Pareja 1: Chumbita/Martinez - Viernes 15-19 o después 22:30
            ("agustinchumbita", "lucasmartinez", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
                {"dias": ["viernes"], "horaInicio": "19:00", "horaFin": "22:30"}
            ]),
            
            # Pareja 2: Córdoba/Aballay - Sábado después 14h
            ("tiagocordoba", "marceloaballay", [
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "14:00"}
            ]),
            
            # Pareja 3: Speziale/Zárate - Sin restricciones
            ("tomasspeziale", "valentinzarate", None),
            
            # Pareja 4: Wamba/Oliva - Viernes después 21h
            ("bautistawamba", "bautistaoliva", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}
            ]),
            
            # Pareja 5: Calderón/Villegas - Sin restricciones
            ("juancalderon", "ignaciovillegas045", None),
            
            # Pareja 6: Vallejos/Medina - Sin restricciones
            ("enzovallejos", "juanmedina", None),
            
            # Pareja 7: Merlo/Fernández - Viernes después 21:30, Sábado después 16h
            ("emilianomerlo", "gabrielfernandez", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:30"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "16:00"}
            ]),
            
            # Pareja 8: Ruarte/Romero - Viernes después 21h
            ("leandroruarte695", "romerogaston451", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}
            ]),
        ]
        
        print(f"\n📋 Parejas a inscribir: {len(parejas_data)}\n")
        
        inscritas = []
        errores = []
        
        for username1, username2, restricciones in parejas_data:
            try:
                j1_id = buscar_jugador(username1)
                j2_id = buscar_jugador(username2)
                
                nombre_pareja = f"{username1}/{username2}"
                
                if not j1_id or not j2_id:
                    print(f"⚠️  {nombre_pareja}: Falta algún jugador")
                    errores.append(f"{nombre_pareja}: Jugadores no encontrados")
                    continue
                
                print(f"Inscribiendo: {nombre_pareja}...")
                
                # Verificar si la pareja ya existe
                pareja_existente = session.execute(
                    text("""
                        SELECT id FROM torneos_parejas 
                        WHERE torneo_id = 37 
                        AND ((jugador1_id = :j1 AND jugador2_id = :j2) 
                             OR (jugador1_id = :j2 AND jugador2_id = :j1))
                    """),
                    {"j1": j1_id, "j2": j2_id}
                ).fetchone()
                
                if pareja_existente:
                    print(f"   ⚠️  Ya existe (ID: {pareja_existente[0]})")
                    continue
                
                # Insertar pareja
                if restricciones:
                    restricciones_json = json.dumps(restricciones)
                    result = session.execute(
                        text("""
                            INSERT INTO torneos_parejas (
                                torneo_id, jugador1_id, jugador2_id, 
                                estado, disponibilidad_horaria, categoria_id
                            )
                            VALUES (37, :j1, :j2, 'confirmada', CAST(:restricciones AS jsonb), :cat_id)
                            RETURNING id
                        """),
                        {
                            "j1": j1_id,
                            "j2": j2_id,
                            "restricciones": restricciones_json,
                            "cat_id": categoria_id
                        }
                    )
                else:
                    result = session.execute(
                        text("""
                            INSERT INTO torneos_parejas (
                                torneo_id, jugador1_id, jugador2_id, 
                                estado, categoria_id
                            )
                            VALUES (37, :j1, :j2, 'confirmada', :cat_id)
                            RETURNING id
                        """),
                        {
                            "j1": j1_id,
                            "j2": j2_id,
                            "cat_id": categoria_id
                        }
                    )
                
                pareja_id = result.fetchone()[0]
                
                print(f"   ✅ Inscrita (ID: {pareja_id})")
                
                restricciones_str = "Sin restricciones" if not restricciones else f"{len(restricciones)} restricción(es)"
                inscritas.append({
                    'id': pareja_id,
                    'nombre': nombre_pareja,
                    'restricciones': restricciones_str
                })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                errores.append(f"{nombre_pareja}: {e}")
                session.rollback()
        
        # Resumen
        print(f"\n{'=' * 80}")
        print(f"📊 RESUMEN:")
        print(f"   ✅ Inscritas: {len(inscritas)}")
        print(f"   ❌ Errores: {len(errores)}")
        print(f"{'=' * 80}")
        
        if inscritas:
            print("\nParejas inscritas:")
            for p in inscritas:
                print(f"  • {p['nombre']} (ID: {p['id']}) - {p['restricciones']}")
        
        if errores:
            print("\nErrores:")
            for e in errores:
                print(f"  • {e}")
        
        if inscritas:
            confirmar = input("\n¿Confirmar inscripciones? (si/no): ").strip().lower()
            
            if confirmar == 'si':
                session.commit()
                print("\n✅ Parejas inscritas exitosamente")
            else:
                session.rollback()
                print("\n❌ Cambios descartados")
        else:
            print("\n⚠️  No se inscribió ninguna pareja")
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    inscribir_parejas_5ta()
