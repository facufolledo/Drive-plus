"""
Script para inscribir parejas en el torneo 37 con sus restricciones horarias
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

def inscribir_parejas_torneo37():
    """Inscribe las 7 parejas en el torneo 37 con sus restricciones"""
    session = Session()
    
    try:
        print("=" * 80)
        print("INSCRIBIR PAREJAS EN TORNEO 37")
        print("=" * 80)
        
        # Verificar que el torneo existe
        torneo = session.execute(
            text("SELECT id, nombre FROM torneos WHERE id = 37")
        ).fetchone()
        
        if not torneo:
            print("❌ El torneo 37 no existe")
            return
        
        print(f"\n✅ Torneo encontrado: {torneo[1]}")
        
        # Obtener la categoría 7ma masculino del torneo 37
        categoria = session.execute(
            text("""
                SELECT id 
                FROM torneo_categorias
                WHERE torneo_id = 37 
                AND nombre = '7ma' 
                AND genero = 'masculino'
            """)
        ).fetchone()
        
        if not categoria:
            print("❌ No se encontró la categoría 7ma masculino en el torneo 37")
            print("\n💡 Categorías disponibles en el torneo 37:")
            cats = session.execute(
                text("SELECT id, nombre, genero FROM torneo_categorias WHERE torneo_id = 37")
            ).fetchall()
            for c in cats:
                print(f"   • ID {c[0]}: {c[1]} ({c[2]})")
            return
        
        categoria_id = categoria[0]
        print(f"✅ Categoría 7ma encontrada (ID: {categoria_id})")
        
        # Buscar IDs de Gustavo Millicay y Federico Montivero (ya existen)
        millicay = session.execute(
            text("SELECT id_usuario FROM usuarios WHERE email LIKE '%millicay%'")
        ).fetchone()
        
        montivero = session.execute(
            text("SELECT id_usuario FROM usuarios WHERE email LIKE '%montivero%'")
        ).fetchone()
        
        # Definir parejas con sus restricciones
        # Formato: (jugador1_id, jugador2_id, nombre_pareja, restricciones)
        parejas = [
            # Pareja 1: Millicay / Montivero (ya existen en la app)
            (millicay[0] if millicay else None, montivero[0] if montivero else None, 
             "Millicay/Montivero", None),
            
            # Pareja 2: Romero Jr / Romero
            (124, 125, "Romero Jr/Romero", None),
            
            # Pareja 3: Bicet / Cejas
            # PUEDEN: Viernes después 19h, Sábado 10-13h y 17-23h
            # RESTRICCIONES: Viernes 09-19h, Sábado 13-17h
            (126, 127, "Bicet/Cejas", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"},
                {"dias": ["sabado"], "horaInicio": "13:00", "horaFin": "17:00"}
            ]),
            
            # Pareja 4: Leterrucci / Guerrero
            # PUEDEN: Viernes después 19h, resto libre
            # RESTRICCIONES: Viernes 09-19h
            (128, 129, "Leterrucci/Guerrero", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
            ]),
            
            # Pareja 5: Barrera / Granillo
            # PUEDEN: Viernes después 17h, Sábado después 17h
            # RESTRICCIONES: Viernes 09-17h, Sábado 09-17h
            (130, 131, "Barrera/Granillo", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "17:00"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "17:00"}
            ]),
            
            # Pareja 6: Sanchez / Bordon (4 jugadores, usar los primeros 2)
            # PUEDEN: Viernes después 19h
            # RESTRICCIONES: Viernes 09-19h
            (132, 133, "Sanchez/Bordon", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
            ]),
            
            # Pareja 7: Giordano / Tapia
            # PUEDEN: Viernes después 15h, Sábado después 15h
            # RESTRICCIONES: Viernes 09-15h, Sábado 09-15h
            (136, 137, "Giordano/Tapia", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "15:00"}
            ]),
        ]
        
        print(f"\n📋 Parejas a inscribir: {len(parejas)}\n")
        
        inscritas = []
        errores = []
        
        for j1_id, j2_id, nombre, restricciones in parejas:
            try:
                if not j1_id or not j2_id:
                    print(f"⚠️  {nombre}: Falta algún jugador")
                    errores.append(f"{nombre}: Jugadores no encontrados")
                    continue
                
                print(f"Inscribiendo: {nombre}...")
                
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
                    'nombre': nombre,
                    'restricciones': restricciones_str
                })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                errores.append(f"{nombre}: {e}")
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
    inscribir_parejas_torneo37()
