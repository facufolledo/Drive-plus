#!/usr/bin/env python3
"""
Inscribir pareja Lucero-Paez en 6ta del torneo 45.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

TORNEO_ID = 45
CATEGORIA_NOMBRE = "6ta"
CATEGORIA_GENERO = "masculino"
RATING_INICIAL = 1299

def inscribir():
    s = Session()
    try:
        print("=" * 70)
        print(f"INSCRIBIR LUCERO-PAEZ - TORNEO {TORNEO_ID} - CATEGORÍA {CATEGORIA_NOMBRE}")
        print("=" * 70)

        # Obtener ID de categoría
        cat = s.execute(text("""
            SELECT id FROM torneo_categorias 
            WHERE torneo_id = :t AND nombre = :n AND genero = :g
        """), {"t": TORNEO_ID, "n": CATEGORIA_NOMBRE, "g": CATEGORIA_GENERO}).fetchone()
        
        if not cat:
            print(f"\n❌ Categoría {CATEGORIA_NOMBRE} {CATEGORIA_GENERO} no encontrada")
            return
        
        CATEGORIA_ID = cat[0]
        print(f"✅ Categoría: {CATEGORIA_NOMBRE} {CATEGORIA_GENERO} (ID: {CATEGORIA_ID})")

        # 1. Buscar Luciano Paez (ya existe en el sistema)
        paez = s.execute(text(
            "SELECT id_usuario FROM usuarios WHERE nombre_usuario LIKE :u"
        ), {"u": "%luciano%paez%"}).fetchone()
        
        if not paez:
            paez = s.execute(text(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario LIKE :u"
            ), {"u": "%paez%"}).fetchone()
        
        if paez:
            paez_id = paez[0]
            print(f"\n✅ Luciano Paez encontrado (ID: {paez_id})")
        else:
            print(f"\n⚠️  Luciano Paez NO encontrado, creando...")
            r = s.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
                VALUES (:u, :e, 'temp_no_login', :rat, :sex, 0)
                RETURNING id_usuario
            """), {"u": "luciano.paez.t45", "e": "luciano.paez.t45@driveplus.temp", "rat": RATING_INICIAL, "sex": "M"})
            paez_id = r.fetchone()[0]
            
            s.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:uid, :nom, :ape, 'Córdoba', 'Argentina')
            """), {"uid": paez_id, "nom": "Luciano", "ape": "Paez"})
            print(f"   ✅ Luciano Paez creado (ID: {paez_id})")

        # 2. Crear Nicolas Lucero
        print(f"\n📝 Creando Nicolas Lucero...")
        existe = s.execute(text(
            "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
        ), {"u": "nicolas.lucero.t45"}).fetchone()

        if existe:
            lucero_id = existe[0]
            print(f"   ⚠️  Nicolas Lucero ya existe (ID: {lucero_id})")
        else:
            r = s.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
                VALUES (:u, :e, 'temp_no_login', :rat, :sex, 0)
                RETURNING id_usuario
            """), {"u": "nicolas.lucero.t45", "e": "nicolas.lucero.t45@driveplus.temp", "rat": RATING_INICIAL, "sex": "M"})
            lucero_id = r.fetchone()[0]

            s.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:uid, :nom, :ape, 'Córdoba', 'Argentina')
            """), {"uid": lucero_id, "nom": "Nicolas", "ape": "Lucero"})

            print(f"   ✅ Nicolas Lucero creado (ID: {lucero_id})")

        s.commit()

        # 3. Inscribir pareja
        print(f"\n👥 Inscribiendo pareja...")

        # Verificar si ya existe
        existe = s.execute(text("""
            SELECT id FROM torneos_parejas
            WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2)
                OR (jugador1_id = :j2 AND jugador2_id = :j1))
        """), {"t": TORNEO_ID, "j1": lucero_id, "j2": paez_id}).fetchone()

        if existe:
            print(f"   ⚠️  Pareja ya existe (ID: {existe[0]})")
            return

        # Restricciones: NO pueden después de las 21:00 jueves y viernes
        restricciones = [
            {"dia": "jueves", "horaInicio": "21:00", "horaFin": "23:59"},
            {"dia": "viernes", "horaInicio": "21:00", "horaFin": "23:59"}
        ]
        
        r = s.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
            VALUES (:t, :c, :j1, :j2, 'confirmada', :disp)
            RETURNING id
        """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": lucero_id, "j2": paez_id, "disp": json.dumps(restricciones)})

        pid = r.fetchone()[0]
        print(f"   ✅ Pareja inscrita (ID: {pid})")
        print(f"   📋 Restricciones: NO pueden después de 21:00 jueves y viernes")

        s.commit()
        print(f"\n{'=' * 70}")
        print(f"✅ LISTO - Pareja Lucero-Paez inscrita en 6ta")
        print("=" * 70)

    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    inscribir()
