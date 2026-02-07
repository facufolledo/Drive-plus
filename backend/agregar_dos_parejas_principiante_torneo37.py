"""
Script para agregar 2 parejas de último momento a Principiante en el torneo 37:
1. Registrar los 4 jugadores en Drive+ (Firebase + BD)
2. Inscribirlos en el torneo 37 categoría Principiante
3. Crear una nueva zona con solo esas 2 parejas
4. Crear el partido entre ellas en el fixture

Editar la configuración debajo con los nombres reales y la fecha/hora del partido.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.config import get_db
from src.models.driveplus_models import Usuario, PerfilUsuario, Partido
from src.models.torneo_models import (
    TorneoPareja, TorneoCategoria, TorneoZona, TorneoZonaPareja, TorneoCancha
)
from src.auth.jwt_handler import JWTHandler
import pytz

load_dotenv()

# --- CONFIGURACIÓN: Editar con los datos reales ---
TORNEO_ID = 37
CREADOR_ID = 2  # Usuario que crea (ej. organizador)

# Pareja 1: (nombre, apellido, sexo) de cada jugador
PAREJA_1 = [
    ("Matias", "Moreno", "M"),
    ("Fernanda", "Bustos", "F"),
]

# Pareja 2
PAREJA_2 = [
    ("Sergio", "Pansa", "M"),
    ("Sebastian", "Corzo", "M"),
]

# Fecha y hora del partido (hora Argentina)
PARTIDO_FECHA_HORA_STR = "2026-02-08 10:00:00"  # formato: YYYY-MM-DD HH:MM:SS

# Nombre de la nueva zona (solo 2 parejas)
NOMBRE_ZONA = "Zona Último Momento"

# --- Firebase (opcional) ---
try:
    import firebase_admin
    from firebase_admin import credentials, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


def inicializar_firebase():
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
    except Exception:
        pass
    return False


def _email(nombre: str, apellido: str) -> str:
    n = nombre.lower().replace(" ", "")
    a = apellido.lower().replace(" ", "")
    return f"{n}.{a}@driveplus.temp"


def _username(nombre: str, apellido: str) -> str:
    return nombre.lower().replace(" ", "") + apellido.lower().replace(" ", "")


def buscar_o_crear_jugador(db: Session, nombre: str, apellido: str, sexo: str, firebase_ok: bool) -> int:
    """Devuelve id_usuario (existente o recién creado)."""
    email = _email(nombre, apellido)
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario:
        print(f"   ✅ {nombre} {apellido}: ya existe (ID {usuario.id_usuario})")
        return usuario.id_usuario

    print(f"   📝 Creando: {nombre} {apellido}...")
    password = "Temporal123!"
    if firebase_ok:
        try:
            firebase_user = auth.create_user(
                email=email,
                password=password,
                display_name=f"{nombre} {apellido}",
                email_verified=True
            )
        except Exception as e:
            if "EMAIL_EXISTS" in str(e):
                firebase_user = auth.get_user_by_email(email)
            else:
                print(f"      ⚠️ Firebase: {e}")

    password_hash = JWTHandler.get_password_hash(password)
    usuario = Usuario(
        email=email,
        nombre_usuario=_username(nombre, apellido),
        password_hash=password_hash,
        sexo=sexo,
        rating=800,  # Principiante
        partidos_jugados=0,
    )
    db.add(usuario)
    db.flush()
    perfil = PerfilUsuario(id_usuario=usuario.id_usuario, nombre=nombre, apellido=apellido)
    db.add(perfil)
    db.flush()
    print(f"      ✅ Creado ID {usuario.id_usuario}")
    return usuario.id_usuario


def inscribir_pareja(db: Session, j1_id: int, j2_id: int, categoria_id: int) -> int:
    """Inscribe pareja en torneo 37 Principiante. Devuelve pareja id."""
    existente = db.query(TorneoPareja).filter(
        TorneoPareja.torneo_id == TORNEO_ID,
        TorneoPareja.categoria_id == categoria_id,
        (
            ((TorneoPareja.jugador1_id == j1_id) & (TorneoPareja.jugador2_id == j2_id)) |
            ((TorneoPareja.jugador1_id == j2_id) & (TorneoPareja.jugador2_id == j1_id))
        ),
    ).first()
    if existente:
        print(f"   ⚠️ Pareja ya inscrita: ID {existente.id}")
        return existente.id

    pareja = TorneoPareja(
        torneo_id=TORNEO_ID,
        categoria_id=categoria_id,
        jugador1_id=j1_id,
        jugador2_id=j2_id,
        estado="confirmada",
        confirmado_jugador1=True,
        confirmado_jugador2=True,
        creado_por_id=CREADOR_ID,
    )
    db.add(pareja)
    db.flush()
    print(f"   ✅ Pareja inscrita: ID {pareja.id}")
    return pareja.id


def run():
    db = next(get_db())
    firebase_ok = inicializar_firebase()
    if not firebase_ok:
        print("⚠️  Firebase no disponible. Jugadores solo en BD.\n")

    try:
        print("\n" + "=" * 70)
        print("AGREGAR 2 PAREJAS PRINCIPIANTE - TORNEO 37 (ÚLTIMO MOMENTO)")
        print("=" * 70 + "\n")

        # 1) Registrar jugadores
        print("1️⃣  Registrando jugadores en Drive+...")
        ids_p1 = [
            buscar_o_crear_jugador(db, p[0], p[1], p[2], firebase_ok) for p in PAREJA_1
        ]
        ids_p2 = [
            buscar_o_crear_jugador(db, p[0], p[1], p[2], firebase_ok) for p in PAREJA_2
        ]
        if len(ids_p1) != 2 or len(ids_p2) != 2:
            print("❌ Faltan IDs de jugadores")
            return

        # 2) Categoría Principiante
        cat = db.query(TorneoCategoria).filter(
            TorneoCategoria.torneo_id == TORNEO_ID,
            TorneoCategoria.nombre == "Principiante",
        ).first()
        if not cat:
            print("❌ Categoría Principiante no encontrada en torneo 37")
            return
        categoria_id = cat.id
        print(f"\n2️⃣  Categoría Principiante: ID {categoria_id}")

        # 3) Inscribir parejas
        print("\n3️⃣  Inscribiendo parejas en el torneo...")
        pareja1_id = inscribir_pareja(db, ids_p1[0], ids_p1[1], categoria_id)
        pareja2_id = inscribir_pareja(db, ids_p2[0], ids_p2[1], categoria_id)

        # 4) Nueva zona y asignar parejas
        print("\n4️⃣  Creando zona y asignando parejas...")
        max_orden = db.query(func.coalesce(func.max(TorneoZona.numero_orden), 0)).filter(
            TorneoZona.torneo_id == TORNEO_ID,
            TorneoZona.categoria_id == categoria_id,
        ).scalar()
        zona = TorneoZona(
            torneo_id=TORNEO_ID,
            categoria_id=categoria_id,
            nombre=NOMBRE_ZONA,
            numero_orden=int(max_orden) + 1,
        )
        db.add(zona)
        db.flush()
        for pareja_id in (pareja1_id, pareja2_id):
            zp = TorneoZonaPareja(zona_id=zona.id, pareja_id=pareja_id)
            db.add(zp)
        print(f"   ✅ Zona creada: {zona.nombre} (ID {zona.id})")

        # 5) Cancha y partido
        print("\n5️⃣  Creando partido en el fixture...")
        cancha = db.query(TorneoCancha).filter(
            TorneoCancha.torneo_id == TORNEO_ID,
            TorneoCancha.activa == True,
        ).first()
        if not cancha:
            print("❌ No hay cancha activa para el torneo 37")
            return

        tz = pytz.timezone("America/Argentina/Buenos_Aires")
        from datetime import datetime
        fecha_naive = datetime.strptime(PARTIDO_FECHA_HORA_STR, "%Y-%m-%d %H:%M:%S")
        fecha_tz = tz.localize(fecha_naive)

        partido = Partido(
            id_torneo=TORNEO_ID,
            categoria_id=categoria_id,
            tipo="torneo",
            fase="zona",
            zona_id=zona.id,
            pareja1_id=pareja1_id,
            pareja2_id=pareja2_id,
            cancha_id=cancha.id,
            fecha_hora=fecha_tz,
            fecha=fecha_tz,
            estado="pendiente",
            creado_por=CREADOR_ID,
            id_creador=CREADOR_ID,
        )
        db.add(partido)
        db.flush()

        print(f"   ✅ Partido creado: ID {partido.id_partido}")
        print(f"      Pareja {pareja1_id} vs Pareja {pareja2_id}")
        print(f"      {PARTIDO_FECHA_HORA_STR} - {cancha.nombre}")

        confirmar = input("\n¿Confirmar todos los cambios? (si/no): ").strip().lower()
        if confirmar == "si":
            db.commit()
            print("\n✅ Listo. Jugadores registrados, parejas inscritas, zona creada y partido en el fixture.")
        else:
            db.rollback()
            print("\n❌ Cambios descartados.")

        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run()
