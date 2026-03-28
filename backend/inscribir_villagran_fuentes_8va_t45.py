#!/usr/bin/env python3
"""
Inscribir pareja Villagran-Fuentes en 8va del torneo 45.
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
CATEGORIA_NOMBRE = "8va"
CATEGORIA_GENERO = "masculino"
RATING_INICIAL = 749

def inscribir():
    s = Session()
    try:
        print("=" * 70)
        print(f"INSCRIBIR VILLAGRAN-FUENTES - TORNEO {TORNEO_ID} - CATEGORÍA {CATEGORIA_NOMBRE}")
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

        # 1. Crear jugadores
        jugadores = [
            {"nombre": "Julian", "apellido": "Villagran", "username": "julian.villagran.t45", "email": "julian.villagran.t45@driveplus.temp", "sexo": "M"},
            {"nombre": "Martin", "apellido": "Fuentes", "username": "martin.fuentes.8va.t45", "email": "martin.fuentes.8va.t45@driveplus.temp", "sexo": "M"},
        ]

        ids = {}
        print(f"\n📝 Creando jugadores...")
        for j in jugadores:
            existe = s.execute(text(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
            ), {"u": j["username"]}).fetchone()

            if existe:
                ids[j["username"]] = existe[0]
                print(f"   ⚠️  {j['nombre']} {j['apellido']} ya existe (ID: {existe[0]})")
                continue

            r = s.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, sexo, partidos_jugados)
                VALUES (:u, :e, 'temp_no_login', :rat, :sex, 0)
                RETURNING id_usuario
            """), {"u": j["username"], "e": j["email"], "rat": RATING_INICIAL, "sex": j["sexo"]})
            uid = r.fetchone()[0]
            ids[j["username"]] = uid

            s.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:uid, :nom, :ape, 'Córdoba', 'Argentina')
            """), {"uid": uid, "nom": j["nombre"], "ape": j["apellido"]})

            print(f"   ✅ {j['nombre']} {j['apellido']} (ID: {uid})")

        s.commit()

        # 2. Inscribir pareja
        print(f"\n👥 Inscribiendo pareja...")
        j1_id = ids.get("julian.villagran.t45")
        j2_id = ids.get("martin.fuentes.8va.t45")

        if not j1_id or not j2_id:
            print(f"   ❌ Jugadores no encontrados")
            return

        # Verificar si ya existe
        existe = s.execute(text("""
            SELECT id FROM torneos_parejas
            WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2)
                OR (jugador1_id = :j2 AND jugador2_id = :j1))
        """), {"t": TORNEO_ID, "j1": j1_id, "j2": j2_id}).fetchone()

        if existe:
            print(f"   ⚠️  Pareja ya existe (ID: {existe[0]})")
            return

        # Sin restricciones
        r = s.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado)
            VALUES (:t, :c, :j1, :j2, 'confirmada')
            RETURNING id
        """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": j1_id, "j2": j2_id})

        pid = r.fetchone()[0]
        print(f"   ✅ Pareja inscrita (ID: {pid})")
        print(f"   📋 Sin restricciones horarias")

        s.commit()
        print(f"\n{'=' * 70}")
        print(f"✅ LISTO - Pareja Villagran-Fuentes inscrita en 8va")
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
