"""
Script para crear jugadores para un torneo
Crea usuarios en Firebase y PostgreSQL con emails generados automáticamente
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
        # Verificar si ya está inicializado
        try:
            firebase_admin.get_app()
            print("✅ Firebase ya inicializado")
            return True
        except ValueError:
            pass
        
        # Intentar inicializar
        service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        if service_account_json:
            creds_dict = json.loads(service_account_json)
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase inicializado con FIREBASE_SERVICE_ACCOUNT")
            return True
        
        # Buscar archivo en el directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.join(script_dir, "firebase-credentials.json")
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"✅ Firebase inicializado con archivo: {cred_path}")
            return True
        
        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if cred_json:
            creds_dict = json.loads(cred_json)
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase inicializado con FIREBASE_CREDENTIALS_JSON")
            return True
        
        print("⚠️  No se encontraron credenciales de Firebase")
        return False
        
    except Exception as e:
        print(f"⚠️  Error al inicializar Firebase: {e}")
        return False

def crear_jugadores():
    """Crea jugadores para el torneo"""
    
    # Inicializar Firebase
    firebase_inicializado = inicializar_firebase()
    
    if not firebase_inicializado:
        print("⚠️  Firebase no disponible. El usuario solo se creará en la BD.")
        print("   Deberás crear el usuario manualmente en Firebase Console.\n")
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("CREAR JUGADORES PARA TORNEO")
        print("=" * 80)
        
        # JUGADORES PARA TORNEO 37 - CATEGORÍA 7MA
        # Formato: (nombre, apellido, sexo, categoria, restricciones)
        # Restricciones: None = sin restricciones, o lista de objetos con dias, horaInicio, horaFin
        
        jugadores = [
            # Pareja 2: Romero Juan Pablo Jr (hijo) / Romero Juan (crear ambos)
            # Nota: Juan Pablo Romero (padre) ya existe en la app
            ("Juan Pablo", "Romero Jr", "M", "7ma", None),
            ("Juan", "Romero", "M", "7ma", None),
            
            # Pareja 3: Bicet Diego / Cejas Juan
            ("Diego", "Bicet", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"},
                {"dias": ["sabado"], "horaInicio": "13:00", "horaFin": "17:00"}
            ]),
            ("Juan", "Cejas", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"},
                {"dias": ["sabado"], "horaInicio": "13:00", "horaFin": "17:00"}
            ]),
            
            # Pareja 4: Eric Leterrucci / Facundo Guerrero
            ("Eric", "Leterrucci", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
            ]),
            ("Facundo", "Guerrero", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
            ]),
            
            # Pareja 5: Barrera Agustín / Granillo Valentín
            ("Agustin", "Barrera", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "17:00"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "17:00"}
            ]),
            ("Valentin", "Granillo", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "17:00"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "17:00"}
            ]),
            
            # Pareja 6: Sanchez Martin / Bordón Andres / De la Fuente Emilio / Coppede Joaquin
            ("Martin", "Sanchez", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
            ]),
            ("Andres", "Bordon", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
            ]),
            ("Emilio", "De la Fuente", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
            ]),
            ("Joaquin", "Coppede", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "19:00"}
            ]),
            
            # Pareja 7: Giordano Matías / Tapia Damian
            ("Matias", "Giordano", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "15:00"}
            ]),
            ("Damian", "Tapia", "M", "7ma", [
                {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
                {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "15:00"}
            ]),
        ]
        
        if not jugadores:
            print("\n⚠️  No hay jugadores para crear")
            print("Edita el script y agrega los jugadores en la lista 'jugadores'")
            return
        
        print(f"\n📋 Jugadores a crear: {len(jugadores)}\n")
        
        creados = []
        errores = []
        
        for nombre, apellido, sexo, categoria, restricciones in jugadores:
            try:
                # Generar email único
                nombre_limpio = nombre.lower().replace(" ", "")
                apellido_limpio = apellido.lower().replace(" ", "")
                email = f"{nombre_limpio}.{apellido_limpio}@driveplus.temp"
                
                # Verificar si ya existe
                usuario_existente = db.query(Usuario).filter(
                    Usuario.email == email
                ).first()
                
                if usuario_existente:
                    print(f"⚠️  {nombre} {apellido}: Ya existe (email: {email})")
                    continue
                
                print(f"Creando: {nombre} {apellido} ({categoria})...")
                
                # 1. Crear en Firebase (si está disponible)
                password = "Temporal123!"  # Password temporal
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
                            # Usuario existe en Firebase, obtener UID
                            firebase_user = auth.get_user_by_email(email)
                            firebase_uid = firebase_user.uid
                            print(f"   ⚠️  Firebase: Ya existía, usando UID {firebase_uid}")
                        else:
                            print(f"   ⚠️  Firebase error: {e}")
                else:
                    print(f"   ⚠️  Firebase no disponible, solo creando en BD")
                
                # 2. Crear en PostgreSQL
                # Hashear password para BD (aunque usemos Firebase)
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
                
                # 3. Crear perfil
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
                    'categoria': categoria,
                    'restricciones': restricciones
                })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                errores.append(f"{nombre} {apellido}: {e}")
                db.rollback()  # Rollback para evitar transacciones bloqueadas
                continue
        
        # Confirmar cambios
        if creados:
            print(f"\n{'=' * 80}")
            print(f"📊 RESUMEN:")
            print(f"   ✅ Creados: {len(creados)}")
            print(f"   ❌ Errores: {len(errores)}")
            print(f"{'=' * 80}")
            
            print("\nJugadores creados:")
            for j in creados:
                restricciones_str = "Sin restricciones" if not j['restricciones'] else f"{len(j['restricciones'])} restricción(es)"
                print(f"  • {j['nombre']} {j['apellido']} (ID: {j['id']}, {j['categoria']}) - {restricciones_str}")
            
            if errores:
                print("\nErrores:")
                for e in errores:
                    print(f"  • {e}")
            
            confirmar = input("\n¿Confirmar creación en la base de datos? (si/no): ").strip().lower()
            
            if confirmar == 'si':
                db.commit()
                print("\n✅ Jugadores creados exitosamente")
                
                # Guardar info para inscripción
                print("\n📋 Información para inscripción:")
                print("ID | Nombre | Restricciones")
                print("-" * 80)
                for j in creados:
                    print(f"{j['id']} | {j['nombre']} {j['apellido']} | {json.dumps(j['restricciones'], ensure_ascii=False) if j['restricciones'] else 'Sin restricciones'}")
                
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
