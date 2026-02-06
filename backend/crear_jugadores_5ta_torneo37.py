"""
Script para crear jugadores de 5ta para torneo 37
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Usuario, PerfilUsuario
from src.auth.jwt_handler import JWTHandler
import json

load_dotenv()

# Importar Firebase Admin
try:
    import firebase_admin
    from firebase_admin import credentials, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️  firebase-admin no está instalado")

def inicializar_firebase():
    """Inicializar Firebase Admin SDK"""
    if not FIREBASE_AVAILABLE:
        return False
    
    try:
        try:
            firebase_admin.get_app()
            print("✅ Firebase ya inicializado")
            return True
        except ValueError:
            pass
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.join(script_dir, "firebase-credentials.json")
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"✅ Firebase inicializado con archivo: {cred_path}")
            return True
        
        print("⚠️  No se encontraron credenciales de Firebase")
        return False
        
    except Exception as e:
        print(f"⚠️  Error al inicializar Firebase: {e}")
        return False

def crear_jugadores():
    """Crea jugadores para categoría 5ta"""
    
    firebase_inicializado = inicializar_firebase()
    
    if not firebase_inicializado:
        print("⚠️  Firebase no disponible. El usuario solo se creará en la BD.")
        print("   Deberás crear el usuario manualmente en Firebase Console.\n")
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("CREAR JUGADORES 5TA - TORNEO 37")
        print("=" * 80)
        
        # Jugadores a crear
        # Formato: (nombre, apellido, sexo, categoria)
        jugadores = [
            # Pareja 1: Chumbita / Martinez
            ("Agustín", "Chumbita", "M", "5ta"),
            ("Lucas", "Martinez", "M", "5ta"),
            
            # Pareja 2: Córdoba / Aballay
            ("Tiago", "Córdoba", "M", "5ta"),
            ("Marcelo", "Aballay", "M", "5ta"),
            
            # Pareja 3: Speziale / Zárate
            ("Tomas", "Speziale", "M", "5ta"),
            ("Valentín", "Zárate", "M", "5ta"),
            
            # Pareja 4: Wamba / Oliva
            ("Bautista", "Wamba", "M", "5ta"),
            ("Bautista", "Oliva", "M", "5ta"),
            
            # Pareja 5: Calderón / Villegas
            ("Juan", "Calderón", "M", "5ta"),
            ("Ignacio", "Villegas", "M", "5ta"),
            
            # Pareja 6: Vallejos / Medina
            ("Enzo", "Vallejos", "M", "5ta"),
            ("Juan", "Medina", "M", "5ta"),
            
            # Pareja 7: Merlo / Fernández
            ("Emiliano", "Merlo", "M", "5ta"),
            ("Gabriel", "Fernández", "M", "5ta"),
            
            # Pareja 8: Ruarte / Romero
            ("Leandro", "Ruarte", "M", "5ta"),
            ("Gaston", "Romero", "M", "5ta"),
        ]
        
        print(f"\n📋 Jugadores a crear: {len(jugadores)}\n")
        
        creados = []
        errores = []
        
        for nombre, apellido, sexo, categoria in jugadores:
            try:
                nombre_limpio = nombre.lower().replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                apellido_limpio = apellido.lower().replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                email = f"{nombre_limpio}.{apellido_limpio}@driveplus.temp"
                
                usuario_existente = db.query(Usuario).filter(
                    Usuario.email == email
                ).first()
                
                if usuario_existente:
                    print(f"⚠️  {nombre} {apellido}: Ya existe (email: {email})")
                    continue
                
                print(f"Creando: {nombre} {apellido} ({categoria})...")
                
                password = "Temporal123!"
                firebase_uid = None
                
                if firebase_inicializado:
                    try:
                        firebase_user = auth.create_user(
                            email=email,
                            password=password,
                            display_name=f"{nombre} {apellido}",
                            email_verified=True
                        )
                        firebase_uid = firebase_user.uid
                        print(f"   ✅ Firebase: {firebase_uid}")
                    except Exception as e:
                        if "EMAIL_EXISTS" in str(e):
                            firebase_user = auth.get_user_by_email(email)
                            firebase_uid = firebase_user.uid
                            print(f"   ⚠️  Firebase: Ya existía, usando UID {firebase_uid}")
                        else:
                            print(f"   ⚠️  Firebase error: {e}")
                else:
                    print(f"   ⚠️  Firebase no disponible, solo creando en BD")
                
                password_hash = JWTHandler.get_password_hash(password)
                
                usuario = Usuario(
                    email=email,
                    nombre_usuario=f"{nombre_limpio}{apellido_limpio}",
                    password_hash=password_hash,
                    sexo=sexo,
                    rating=1200
                )
                db.add(usuario)
                db.flush()
                
                perfil = PerfilUsuario(
                    id_usuario=usuario.id_usuario,
                    nombre=nombre,
                    apellido=apellido
                )
                db.add(perfil)
                db.flush()
                
                print(f"   ✅ PostgreSQL: Usuario ID {usuario.id_usuario}")
                
                creados.append({
                    'id': usuario.id_usuario,
                    'nombre': nombre,
                    'apellido': apellido,
                    'email': email,
                    'categoria': categoria
                })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                errores.append(f"{nombre} {apellido}: {e}")
                db.rollback()
                continue
        
        if creados:
            print(f"\n{'=' * 80}")
            print(f"📊 RESUMEN:")
            print(f"   ✅ Creados: {len(creados)}")
            print(f"   ❌ Errores: {len(errores)}")
            print(f"{'=' * 80}")
            
            print("\nJugadores creados:")
            for j in creados:
                print(f"  • {j['nombre']} {j['apellido']} (ID: {j['id']}, {j['categoria']})")
            
            if errores:
                print("\nErrores:")
                for e in errores:
                    print(f"  • {e}")
            
            confirmar = input("\n¿Confirmar creación en la base de datos? (si/no): ").strip().lower()
            
            if confirmar == 'si':
                db.commit()
                print("\n✅ Jugadores creados exitosamente")
                print("\n📝 Ahora ejecuta: python inscribir_parejas_5ta_torneo37.py")
            else:
                db.rollback()
                print("\n❌ Cambios descartados")
        else:
            print("\n⚠️  No se creó ningún jugador")
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    crear_jugadores()
