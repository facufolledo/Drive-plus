"""
Script para inscribir nuevas parejas al torneo 37 con restricciones horarias
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from src.database.config import get_db
from src.models.driveplus_models import Usuario, PerfilUsuario
from src.models.torneo_models import TorneoPareja, TorneoCategoria
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
            return True
        except ValueError:
            pass
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.join(script_dir, "firebase-credentials.json")
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            return True
        
        return False
        
    except Exception as e:
        return False

def buscar_o_crear_usuario(db, nombre, apellido, username, firebase_inicializado):
    """Busca un usuario por username o lo crea si no existe"""
    # Buscar por username
    usuario = db.query(Usuario).filter(
        Usuario.nombre_usuario == username
    ).first()
    
    if usuario:
        print(f"✅ Usuario encontrado: {nombre} {apellido} (@{username}) - ID: {usuario.id_usuario}")
        return usuario.id_usuario
    
    # Crear nuevo usuario
    print(f"📝 Creando usuario: {nombre} {apellido} (@{username})")
    
    nombre_limpio = nombre.lower().replace(" ", "")
    apellido_limpio = apellido.lower().replace(" ", "")
    email = f"{nombre_limpio}.{apellido_limpio}@driveplus.temp"
    password = "Temporal123!"
    
    # Crear en Firebase si está disponible
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
        except Exception as e:
            if "EMAIL_EXISTS" in str(e):
                firebase_user = auth.get_user_by_email(email)
                firebase_uid = firebase_user.uid
    
    # Crear en PostgreSQL
    password_hash = JWTHandler.get_password_hash(password)
    
    usuario = Usuario(
        email=email,
        nombre_usuario=username,
        password_hash=password_hash,
        sexo="M",
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
    db.commit()
    
    print(f"✅ Usuario creado: {nombre} {apellido} - ID: {usuario.id_usuario}")
    return usuario.id_usuario

def inscribir_pareja(db, jugador1_id, jugador2_id, categoria_nombre, disponibilidad_horaria, nombre_pareja):
    """Inscribe una pareja en el torneo con restricciones horarias"""
    
    TORNEO_ID = 37
    
    # Obtener categoría
    categoria = db.query(TorneoCategoria).filter(
        TorneoCategoria.torneo_id == TORNEO_ID,
        TorneoCategoria.nombre == categoria_nombre
    ).first()
    
    if not categoria:
        print(f"❌ Categoría '{categoria_nombre}' no encontrada")
        return None
    
    # Verificar si ya existe la pareja
    pareja_existente = db.query(TorneoPareja).filter(
        TorneoPareja.torneo_id == TORNEO_ID,
        TorneoPareja.categoria_id == categoria.id,
        (
            ((TorneoPareja.jugador1_id == jugador1_id) & (TorneoPareja.jugador2_id == jugador2_id)) |
            ((TorneoPareja.jugador1_id == jugador2_id) & (TorneoPareja.jugador2_id == jugador1_id))
        )
    ).first()
    
    if pareja_existente:
        print(f"⚠️  Pareja ya existe: ID {pareja_existente.id}")
        return pareja_existente.id
    
    # Crear pareja
    pareja = TorneoPareja(
        torneo_id=TORNEO_ID,
        categoria_id=categoria.id,
        jugador1_id=jugador1_id,
        jugador2_id=jugador2_id,
        estado='confirmada',
        confirmado_jugador1=True,
        confirmado_jugador2=True,
        creado_por_id=2,  # facufolledo7
        disponibilidad_horaria=disponibilidad_horaria
    )
    
    db.add(pareja)
    db.commit()
    db.refresh(pareja)
    
    print(f"✅ Pareja inscrita: {nombre_pareja} - ID: {pareja.id}")
    print(f"   Restricciones: {len(disponibilidad_horaria)} franjas horarias")
    for idx, franja in enumerate(disponibilidad_horaria, 1):
        print(f"      {idx}. {franja['dias']}: {franja['horaInicio']} - {franja['horaFin']}")
    
    return pareja.id

def main():
    firebase_inicializado = inicializar_firebase()
    db = next(get_db())
    
    try:
        print("\n" + "="*80)
        print("🎾 INSCRIPCIÓN DE NUEVAS PAREJAS - TORNEO 37")
        print("="*80 + "\n")
        
        # ============================================
        # PAREJA 1 - 7MA: Molina Nahuel / Campos Cristian
        # ============================================
        print("\n📋 PAREJA 1 - 7MA: Molina Nahuel / Campos Cristian")
        print("-" * 80)
        
        # Buscar o crear usuarios
        molina_id = buscar_o_crear_usuario(db, "Nahuel", "Molina", "nahuelmolina", firebase_inicializado)
        campos_id = buscar_o_crear_usuario(db, "Cristian", "Campos", "cristiancampos", firebase_inicializado)
        
        # Restricciones: No pueden viernes, sábado después de las 15:00
        restricciones_pareja1 = [
            {
                "dias": ["sabado"],
                "horaInicio": "15:00",
                "horaFin": "23:30"
            }
        ]
        
        inscribir_pareja(
            db, molina_id, campos_id, "7ma",
            restricciones_pareja1,
            "Molina / Campos"
        )
        
        # ============================================
        # PAREJA 2 - 7MA: Leandro Ruarte / Bautista Oliva
        # ============================================
        print("\n📋 PAREJA 2 - 7MA: Leandro Ruarte / Bautista Oliva")
        print("-" * 80)
        
        # Buscar usuarios existentes
        ruarte = db.query(Usuario).join(PerfilUsuario).filter(
            PerfilUsuario.nombre == "Leandro",
            PerfilUsuario.apellido == "Ruarte"
        ).first()
        
        oliva = db.query(Usuario).join(PerfilUsuario).filter(
            PerfilUsuario.nombre == "Bautista",
            PerfilUsuario.apellido == "Oliva"
        ).first()
        
        if not ruarte:
            print("❌ Leandro Ruarte no encontrado en la app")
            ruarte_id = buscar_o_crear_usuario(db, "Leandro", "Ruarte", "leandroruarte", firebase_inicializado)
        else:
            ruarte_id = ruarte.id_usuario
            print(f"✅ Leandro Ruarte encontrado - ID: {ruarte_id}")
        
        if not oliva:
            print("❌ Bautista Oliva no encontrado en la app")
            oliva_id = buscar_o_crear_usuario(db, "Bautista", "Oliva", "bautistaoliva", firebase_inicializado)
        else:
            oliva_id = oliva.id_usuario
            print(f"✅ Bautista Oliva encontrado - ID: {oliva_id}")
        
        # Restricciones: No pueden viernes, sábado después de las 16:00
        restricciones_pareja2 = [
            {
                "dias": ["sabado"],
                "horaInicio": "16:00",
                "horaFin": "23:30"
            }
        ]
        
        inscribir_pareja(
            db, ruarte_id, oliva_id, "7ma",
            restricciones_pareja2,
            "Ruarte / Oliva"
        )
        
        # ============================================
        # PAREJA 3 - PRINCIPIANTE: Jere Vera / Marcos Calderón
        # ============================================
        print("\n📋 PAREJA 3 - PRINCIPIANTE: Jere Vera / Marcos Calderón")
        print("-" * 80)
        
        # Buscar o crear usuarios
        vera_id = buscar_o_crear_usuario(db, "Jere", "Vera", "jerevera", firebase_inicializado)
        calderon_id = buscar_o_crear_usuario(db, "Marcos", "Calderón", "marcoscalderon", firebase_inicializado)
        
        # Restricciones: No pueden viernes, sábado después de las 10:00
        restricciones_pareja3 = [
            {
                "dias": ["sabado"],
                "horaInicio": "10:00",
                "horaFin": "23:30"
            }
        ]
        
        inscribir_pareja(
            db, vera_id, calderon_id, "Principiante",
            restricciones_pareja3,
            "Vera / Calderón"
        )
        
        print("\n" + "="*80)
        print("✅ PROCESO COMPLETADO")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
