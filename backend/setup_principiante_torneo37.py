"""
Script completo para crear jugadores de Principiante e inscribirlos en torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
from passlib.context import CryptContext

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def setup_principiante():
    """Crea jugadores e inscribe parejas de Principiante"""
    session = Session()
    
    try:
        print("=" * 80)
        print("SETUP PRINCIPIANTE - TORNEO 37")
        print("=" * 80)
        
        # Hashear password
        password_hash = pwd_context.hash("Temporal123!")
        
        # Buscar IDs de jugadores que ya existen
        villafane = session.execute(text("SELECT id_usuario FROM usuarios WHERE email LIKE '%villafane%' OR email LIKE '%villafañe%'")).fetchone()
        cavalleri = session.execute(text("SELECT id_usuario FROM usuarios WHERE email LIKE '%cavalleri%'")).fetchone()
        vega = session.execute(text("SELECT id_usuario FROM usuarios WHERE email LIKE '%vega%' AND email LIKE '%matias%'")).fetchone()
        
        print(f"\n✅ Jugadores existentes encontrados:")
        if villafane:
            print(f"   • Villafañe: ID {villafane[0]}")
        if cavalleri:
            print(f"   • Cavalleri: ID {cavalleri[0]}")
        if vega:
            print(f"   • Vega: ID {vega[0]}")
        
        # Jugadores a crear
        jugadores_nuevos = [
            ("Franco", "Direnzo", "M"),
            ("Maximiliano", "Yelamo", "M"),
            ("Jorge", "Paz", "M"),
            ("Rodrigo", "Paez", "M"),
            ("Mikea", "Gonzalez", "M"),
            ("Gula", "Saracho", "F"),
            ("Benja", "Reynoso", "M"),
            ("Valentino", "Alcaraz", "M"),
            ("Leonel", "Cordoba", "M"),
            ("Gabriel", "Gallo", "M"),
            ("Victor", "Gonzalez", "M"),
            ("Nicolas", "Gonzalez", "M"),
            ("Santino", "Molina", "M"),
            ("Agustin", "Martinez", "M"),
            ("David", "Mazza", "M"),
            ("David", "Ferreyra", "M"),
            ("Exequiel", "Damian", "M"),
            ("Santiago", "Mazza", "M"),
            ("Dario", "Barrionuevo", "M"),
        ]
        
        print(f"\n📋 Creando {len(jugadores_nuevos)} jugadores nuevos...")
        
        ids_creados = {}
        for nombre, apellido, sexo in jugadores_nuevos:
            email = f"{nombre.lower()}.{apellido.lower()}@driveplus.temp"
            username = f"{nombre.lower()}{apellido.lower()}"
            
            # Verificar si ya existe
            existe = session.execute(
                text("SELECT id_usuario FROM usuarios WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if existe:
                print(f"   ⚠️  {nombre} {apellido}: Ya existe")
                ids_creados[f"{nombre}_{apellido}"] = existe[0]
                continue
            
            # Crear usuario
            result = session.execute(
                text("""
                    INSERT INTO usuarios (nombre_usuario, email, password_hash, sexo, rating, partidos_jugados)
                    VALUES (:username, :email, :password_hash, :sexo, 1200, 0)
                    RETURNING id_usuario
                """),
                {"username": username, "email": email, "password_hash": password_hash, "sexo": sexo}
            )
            user_id = result.fetchone()[0]
            
            # Crear perfil
            session.execute(
                text("""
                    INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
                    VALUES (:user_id, :nombre, :apellido)
                """),
                {"user_id": user_id, "nombre": nombre, "apellido": apellido}
            )
            
            ids_creados[f"{nombre}_{apellido}"] = user_id
            print(f"   ✅ {nombre} {apellido}: ID {user_id}")
        
        session.commit()
        print(f"\n✅ Jugadores creados exitosamente")
        
        # Obtener ID de categoría Principiante
        cat = session.execute(
            text("SELECT id FROM torneo_categorias WHERE torneo_id = 37 AND nombre = 'Principiante'")
        ).fetchone()
        
        if not cat:
            print("\n❌ No se encontró la categoría Principiante en el torneo 37")
            return
        
        cat_id = cat[0]
        
        # Definir parejas con restricciones
        parejas = [
            # Pareja 1
            (villafane[0] if villafane else None, ids_creados.get("Franco_Direnzo"),
             "Villafañe/Direnzo", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "17:00"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "17:00"}
            ]),
            
            # Pareja 2
            (ids_creados.get("Maximiliano_Yelamo"), ids_creados.get("Jorge_Paz"),
             "Yelamo/Paz", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
            ]),
            
            # Pareja 3
            (ids_creados.get("Rodrigo_Paez"), ids_creados.get("Mikea_Gonzalez"),
             "Paez/González", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "21:00"}
            ]),
            
            # Pareja 4
            (cavalleri[0] if cavalleri else None, ids_creados.get("Gula_Saracho"),
             "Cavalleri/Saracho", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"}
            ]),
            
            # Pareja 5
            (ids_creados.get("Benja_Reynoso"), ids_creados.get("Valentino_Alcaraz"),
             "Reynoso/Alcaraz", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "22:30"}
            ]),
            
            # Pareja 6
            (ids_creados.get("Leonel_Cordoba"), ids_creados.get("Gabriel_Gallo"),
             "Córdoba/Gallo", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "18:00"}
            ]),
            
            # Pareja 7
            (ids_creados.get("Victor_Gonzalez"), ids_creados.get("Nicolas_Gonzalez"),
             "González/González", [
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "10:00"}
            ]),
            
            # Pareja 8 - SOLO viernes 14-17h, resto libre
            (ids_creados.get("Santino_Molina"), ids_creados.get("Agustin_Martinez"),
             "Molina/Martinez", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "14:00"},
                {"dias": ["viernes"], "horaInicio": "17:00", "horaFin": "23:30"}
            ]),
            
            # Pareja 9 - SOLO viernes 14-18h, resto libre
            (ids_creados.get("David_Mazza"), ids_creados.get("David_Ferreyra"),
             "Mazza/Ferreyra", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "14:00"},
                {"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "23:30"}
            ]),
            
            # Pareja 10 - Sin restricciones
            (ids_creados.get("Exequiel_Damian"), ids_creados.get("Santiago_Mazza"),
             "Damian/Mazza", None),
            
            # Pareja 11 - SOLO viernes 16-22h, resto libre
            (ids_creados.get("Dario_Barrionuevo"), vega[0] if vega else None,
             "Barrionuevo/Vega", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "16:00"},
                {"dias": ["viernes"], "horaInicio": "22:00", "horaFin": "23:30"}
            ]),
        ]
        
        print(f"\n📋 Inscribiendo {len(parejas)} parejas...")
        
        inscritas = 0
        for j1_id, j2_id, nombre, restricciones in parejas:
            if not j1_id or not j2_id:
                print(f"   ⚠️  {nombre}: Falta algún jugador")
                continue
            
            restricciones_json = json.dumps(restricciones) if restricciones else None
            
            if restricciones_json:
                result = session.execute(
                    text("""
                        INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id, estado, categoria_id, disponibilidad_horaria)
                        VALUES (37, :j1, :j2, 'confirmada', :cat_id, CAST(:restricciones AS jsonb))
                        RETURNING id
                    """),
                    {"j1": j1_id, "j2": j2_id, "cat_id": cat_id, "restricciones": restricciones_json}
                )
            else:
                result = session.execute(
                    text("""
                        INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id, estado, categoria_id)
                        VALUES (37, :j1, :j2, 'confirmada', :cat_id)
                        RETURNING id
                    """),
                    {"j1": j1_id, "j2": j2_id, "cat_id": cat_id}
                )
            
            pareja_id = result.fetchone()[0]
            restricciones_str = f"{len(restricciones)} restricción(es)" if restricciones else "Sin restricciones"
            print(f"   ✅ {nombre}: ID {pareja_id} - {restricciones_str}")
            inscritas += 1
        
        session.commit()
        
        print(f"\n{'=' * 80}")
        print(f"✅ SETUP COMPLETADO")
        print(f"{'=' * 80}")
        print(f"\n📊 Resumen:")
        print(f"   • Jugadores creados: {len(ids_creados)}")
        print(f"   • Parejas inscritas: {inscritas}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    setup_principiante()
