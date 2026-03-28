"""
Inscribir 5 parejas adicionales en categoría 7ma del torneo 46
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine, text

env_file = os.path.join(os.path.dirname(__file__), '.env.production')
DATABASE_URL = None
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DATABASE_URL = line.split('=', 1)[1].strip().strip('"').strip("'")
                break

engine = create_engine(DATABASE_URL)

TORNEO_ID = 46

# Jugadores nuevos a crear
NUEVOS_JUGADORES = [
    {"nombre": "Federico", "apellido": "Millicay", "username": "federico.millicay.t46"},
    {"nombre": "Exequiel", "apellido": "Carrizo", "username": "exequiel.carrizo.t46"},
    {"nombre": "Dante", "apellido": "Saldaño", "username": "dante.saldano.t46"},
    {"nombre": "Alejandro", "apellido": "Vásquez", "username": "alejandro.vasquez.t46"},
    {"nombre": "Renzo", "apellido": "Gonzales", "username": "renzo.gonzales.t46"},
    {"nombre": "Erik", "apellido": "Letterucci", "username": "erik.letterucci.t46"},
    {"nombre": "Exequiel", "apellido": "Diaz", "username": "exequiel.diaz.t46"},
    {"nombre": "Yamil", "apellido": "Jofre", "username": "yamil.jofre.t46"},
    {"nombre": "Leo", "apellido": "Diaz", "username": "leo.diaz.t46"},
    {"nombre": "Valentín", "apellido": "Barroca", "username": "valentin.barroca.t46"},
]

# Parejas con restricciones
PAREJAS = [
    # Millicay Federico + Carrizo Exequiel - viernes +20:30
    ("federico.millicay.t46", "exequiel.carrizo.t46", 
     [{"dias": ["viernes"], "horaInicio": "20:30", "horaFin": "23:59"}]),
    
    # Saldaño Dante + Vásquez Alejandro - viernes +17
    ("dante.saldano.t46", "alejandro.vasquez.t46",
     [{"dias": ["viernes"], "horaInicio": "17:00", "horaFin": "23:59"}]),
    
    # Gonzales Renzo + Letterucci Erik - viernes +18, sábado +15
    ("renzo.gonzales.t46", "erik.letterucci.t46",
     [{"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "23:59"},
      {"dias": ["sabado"], "horaInicio": "15:00", "horaFin": "23:59"}]),
    
    # Diaz Exequiel + Jofre Yamil - viernes +22, sábado +17
    ("exequiel.diaz.t46", "yamil.jofre.t46",
     [{"dias": ["viernes"], "horaInicio": "22:00", "horaFin": "23:59"},
      {"dias": ["sabado"], "horaInicio": "17:00", "horaFin": "23:59"}]),
    
    # Diaz Leo + Barroca Valentín - viernes +23
    ("leo.diaz.t46", "valentin.barroca.t46",
     [{"dias": ["viernes"], "horaInicio": "23:00", "horaFin": "23:59"}]),
]

def main():
    print("=" * 80)
    print(f"INSCRIPCIÓN ADICIONAL TORNEO {TORNEO_ID} - 7MA (5 PAREJAS)")
    print("=" * 80)
    
    with engine.connect() as conn:
        # 1. Verificar torneo y categoría
        torneo = conn.execute(text("SELECT id, nombre FROM torneos WHERE id = :tid"), {"tid": TORNEO_ID}).fetchone()
        if not torneo:
            print(f"❌ ERROR: Torneo {TORNEO_ID} no encontrado")
            return
        print(f"✅ Torneo: {torneo.nombre}")
        
        cat = conn.execute(text("""
            SELECT id, nombre 
            FROM torneo_categorias
            WHERE torneo_id = :tid AND nombre = '7ma'
        """), {"tid": TORNEO_ID}).fetchone()
        
        if not cat:
            print("❌ ERROR: Categoría 7ma no encontrada en el torneo")
            return
        CATEGORIA_ID = cat.id
        print(f"✅ Categoría 7ma del torneo: ID {CATEGORIA_ID}")
        
        cat_general = conn.execute(text("SELECT id_categoria FROM categorias WHERE nombre = '7ma'")).fetchone()
        CATEGORIA_GENERAL_ID = cat_general.id_categoria
        print(f"✅ Categoría 7ma general: ID {CATEGORIA_GENERAL_ID}")
        
        # 2. Crear usuarios nuevos
        print("\n" + "=" * 80)
        print("CREANDO USUARIOS TEMPORALES")
        print("=" * 80)
        
        nuevos_ids = {}
        for j in NUEVOS_JUGADORES:
            existe = conn.execute(text(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
            ), {"u": j["username"]}).fetchone()
            
            if existe:
                nuevos_ids[j["username"]] = existe[0]
                print(f"⚠️  {j['nombre']} {j['apellido']} ya existe (ID: {existe[0]})")
                continue
            
            result = conn.execute(text("""
                INSERT INTO usuarios (nombre_usuario, email, password_hash, rating, id_categoria, es_administrador, sexo, partidos_jugados)
                VALUES (:u, :e, 'temp_no_login', 1500, :cat, false, 'M', 0)
                RETURNING id_usuario
            """), {
                "u": j["username"],
                "e": f"{j['username']}@driveplus.temp",
                "cat": CATEGORIA_GENERAL_ID
            })
            user_id = result.fetchone()[0]
            
            conn.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:id, :nombre, :apellido, 'Córdoba', 'Argentina')
            """), {"id": user_id, "nombre": j["nombre"], "apellido": j["apellido"]})
            
            nuevos_ids[j["username"]] = user_id
            print(f"✅ ID {user_id} - {j['nombre']} {j['apellido']}")
        
        conn.commit()
        
        # 3. Inscribir parejas
        print("\n" + "=" * 80)
        print("INSCRIBIENDO PAREJAS")
        print("=" * 80)
        
        for i, (j1, j2, restricciones) in enumerate(PAREJAS, 1):
            id1 = nuevos_ids[j1]
            id2 = nuevos_ids[j2]
            
            u1 = conn.execute(text("SELECT nombre_usuario FROM usuarios WHERE id_usuario = :id"), {"id": id1}).fetchone()
            u2 = conn.execute(text("SELECT nombre_usuario FROM usuarios WHERE id_usuario = :id"), {"id": id2}).fetchone()
            
            nombre_pareja = f"{u1[0]} + {u2[0]}"
            
            existe = conn.execute(text("""
                SELECT id FROM torneos_parejas
                WHERE torneo_id = :tid AND categoria_id = :cid
                  AND ((jugador1_id = :j1 AND jugador2_id = :j2) OR (jugador1_id = :j2 AND jugador2_id = :j1))
            """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID, "j1": id1, "j2": id2}).fetchone()
            
            if existe:
                print(f"⚠️  Pareja {i} ya existe (ID: {existe[0]})")
                continue
            
            restr_json = json.dumps(restricciones) if restricciones else None
            
            if restr_json:
                result = conn.execute(text("""
                    INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
                    VALUES (:tid, :cid, :j1, :j2, 'confirmada', CAST(:r AS jsonb))
                    RETURNING id
                """), {
                    "tid": TORNEO_ID,
                    "cid": CATEGORIA_ID,
                    "j1": id1,
                    "j2": id2,
                    "r": restr_json
                })
            else:
                result = conn.execute(text("""
                    INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado)
                    VALUES (:tid, :cid, :j1, :j2, 'confirmada')
                    RETURNING id
                """), {
                    "tid": TORNEO_ID,
                    "cid": CATEGORIA_ID,
                    "j1": id1,
                    "j2": id2
                })
            
            pareja_id = result.fetchone()[0]
            n_restr = len(restricciones) if restricciones else 0
            print(f"✅ Pareja {i} creada (ID: {pareja_id}) - {nombre_pareja} - {n_restr} restricción(es)")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ INSCRIPCIÓN COMPLETADA")
        print("=" * 80)
        
        total = conn.execute(text("""
            SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :tid AND categoria_id = :cid
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchone()
        
        print(f"Total parejas en 7ma: {total[0]}")

if __name__ == "__main__":
    main()
