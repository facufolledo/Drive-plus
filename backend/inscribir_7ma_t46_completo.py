"""
Inscribir parejas en categoría 7ma del torneo 46
Crea usuarios temp para los que no existen
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text

# Leer DATABASE_URL del archivo .env.production
env_file = os.path.join(os.path.dirname(__file__), '.env.production')
DATABASE_URL = None
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DATABASE_URL = line.split('=', 1)[1].strip().strip('"').strip("'")
                break

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL no encontrada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

TORNEO_ID = 46

# Jugadores que NO existen (crear como temp)
NUEVOS_JUGADORES = [
    {"nombre": "Emiliano", "apellido": "Lucero", "username": "emiliano.lucero.t46"},
    {"nombre": "Lucas", "apellido": "Apostolo", "username": "lucas.apostolo.t46"},
    {"nombre": "Mariano", "apellido": "Roldán", "username": "mariano.roldan.t46"},
    {"nombre": "Mariano", "apellido": "Cruz", "username": "mariano.cruz.t46"},
    {"nombre": "Lucas", "apellido": "Juin", "username": "lucas.juin.t46"},
    {"nombre": "Tiago", "apellido": "López", "username": "tiago.lopez.t46"},
    {"nombre": "Imanol", "apellido": "Yaryura", "username": "imanol.yaryura.t46"},
    {"nombre": "Esteban", "apellido": "Bedini", "username": "esteban.bedini.t46"},
    {"nombre": "Benicio", "apellido": "Johannesen", "username": "benicio.johannesen.t46"},
    {"nombre": "Joselin", "apellido": "Silva", "username": "joselin.silva.t46"},
    {"nombre": "Dilan", "apellido": "Aguilar", "username": "dilan.aguilar.t46"},
    {"nombre": "Nazareno", "apellido": "Diaz", "username": "nazareno.diaz.t46"},
    {"nombre": "Ismael", "apellido": "Salido", "username": "ismael.salido.t46"},
    {"nombre": "Aron", "apellido": "Brizuela", "username": "aron.brizuela.t46"},
    {"nombre": "Valentín", "apellido": "Moreno", "username": "valentin.moreno.t46"},
    {"nombre": "Axel", "apellido": "Alfaro", "username": "axel.alfaro.t46"},
    {"nombre": "Matías", "apellido": "Alfaro", "username": "matias.alfaro.t46"},
    {"nombre": "Marcelo", "apellido": "Aguilar", "username": "marcelo.aguilar.t46"},
    {"nombre": "Agustín", "apellido": "Mercado", "username": "agustin.mercado.t46"},
    {"nombre": "Cesar", "apellido": "Zaracho", "username": "cesar.zaracho.t46"},
    {"nombre": "Leonardo", "apellido": "Villarrubia", "username": "leonardo.villarrubia.t46"},
    {"nombre": "Alberto", "apellido": "Ibañaz", "username": "alberto.ibanaz.t46"},
    {"nombre": "Mariano", "apellido": "Nieto", "username": "mariano.nieto.t46"},
    {"nombre": "Federico", "apellido": "Olivera", "username": "federico.olivera.t46"},
    {"nombre": "Martín", "apellido": "Aredes", "username": "martin.aredes.t46"},
    {"nombre": "Matías", "apellido": "Aredes", "username": "matias.aredes.t46"},
]

# Parejas: (j1_id_o_username, j2_id_o_username, restricciones_horarias)
# restricciones = lista de horarios NO disponibles
PAREJAS = [
    ("emiliano.lucero.t46", 2, [{"dias": ["viernes"], "horaInicio": "16:00", "horaFin": "23:59"}]),
    (495, 43, [{"dias": ["viernes"], "horaInicio": "19:00", "horaFin": "23:59"}, {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "20:00"}]),
    (30, 85, [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "17:00"}, {"dias": ["viernes"], "horaInicio": "22:00", "horaFin": "23:59"}, {"dias": ["sabado"], "horaInicio": "19:00", "horaFin": "23:59"}]),
    ("lucas.apostolo.t46", "mariano.roldan.t46", [{"dias": ["viernes"], "horaInicio": "17:00", "horaFin": "22:00"}]),
    (56, "mariano.cruz.t46", [{"dias": ["viernes"], "horaInicio": "20:00", "horaFin": "23:59"}]),
    (5, 55, [{"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "18:59"}]),
    ("lucas.juin.t46", "tiago.lopez.t46", [{"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "23:59"}, {"dias": ["sabado"], "horaInicio": "12:00", "horaFin": "23:59"}]),
    ("imanol.yaryura.t46", 11, []),
    ("esteban.bedini.t46", "benicio.johannesen.t46", [{"dias": ["viernes"], "horaInicio": "14:00", "horaFin": "23:59"}, {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "17:00"}]),
    ("joselin.silva.t46", "dilan.aguilar.t46", [{"dias": ["viernes"], "horaInicio": "00:30", "horaFin": "00:59"}, {"dias": ["sabado"], "horaInicio": "14:00", "horaFin": "23:59"}]),
    ("nazareno.diaz.t46", "ismael.salido.t46", [{"dias": ["sabado"], "horaInicio": "12:00", "horaFin": "23:59"}]),
    (80, 81, [{"dias": ["viernes"], "horaInicio": "19:00", "horaFin": "23:59"}]),
    ("aron.brizuela.t46", "valentin.moreno.t46", [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "23:59"}]),
    ("axel.alfaro.t46", "matias.alfaro.t46", [{"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "23:59"}]),
    (1027, "marcelo.aguilar.t46", [{"dias": ["viernes"], "horaInicio": "15:00", "horaFin": "23:59"}]),
    ("agustin.mercado.t46", "cesar.zaracho.t46", [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "23:59"}]),
    ("leonardo.villarrubia.t46", "alberto.ibanaz.t46", [{"dias": ["viernes"], "horaInicio": "20:00", "horaFin": "23:59"}]),
    ("mariano.nieto.t46", "federico.olivera.t46", [{"dias": ["sabado"], "horaInicio": "14:00", "horaFin": "23:59"}]),
    ("martin.aredes.t46", "matias.aredes.t46", [{"dias": ["viernes"], "horaInicio": "14:00", "horaFin": "22:00"}]),
]

def main():
    print("=" * 80)
    print(f"INSCRIPCIÓN TORNEO {TORNEO_ID} - 7MA")
    print("=" * 80)
    
    with engine.connect() as conn:
        # 1. Verificar que el torneo existe
        torneo = conn.execute(text("SELECT id, nombre FROM torneos WHERE id = :tid"), {"tid": TORNEO_ID}).fetchone()
        if not torneo:
            print(f"❌ ERROR: Torneo {TORNEO_ID} no encontrado")
            return
        print(f"✅ Torneo: {torneo.nombre}")
        
        # 2. Obtener categoria_id de torneo_categorias
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
        
        # 3. Obtener id_categoria de la tabla categorias (para usuarios)
        cat_general = conn.execute(text("SELECT id_categoria FROM categorias WHERE nombre = '7ma'")).fetchone()
        if not cat_general:
            print("❌ ERROR: Categoría 7ma no encontrada en categorias generales")
            return
        CATEGORIA_GENERAL_ID = cat_general.id_categoria
        print(f"✅ Categoría 7ma general: ID {CATEGORIA_GENERAL_ID}")
        
        # 4. Crear usuarios nuevos
        print("\n" + "=" * 80)
        print("CREANDO USUARIOS TEMPORALES")
        print("=" * 80)
        
        nuevos_ids = {}
        for j in NUEVOS_JUGADORES:
            # Verificar si ya existe
            existe = conn.execute(text(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario = :u"
            ), {"u": j["username"]}).fetchone()
            
            if existe:
                nuevos_ids[j["username"]] = existe[0]
                print(f"⚠️  {j['nombre']} {j['apellido']} ya existe (ID: {existe[0]})")
                continue
            
            # Crear usuario con rating inicial
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
            
            # Crear perfil
            conn.execute(text("""
                INSERT INTO perfil_usuarios (id_usuario, nombre, apellido, ciudad, pais)
                VALUES (:id, :nombre, :apellido, 'Córdoba', 'Argentina')
            """), {"id": user_id, "nombre": j["nombre"], "apellido": j["apellido"]})
            
            nuevos_ids[j["username"]] = user_id
            print(f"✅ ID {user_id} - {j['nombre']} {j['apellido']}")
        
        conn.commit()
        
        # 5. Inscribir parejas
        print("\n" + "=" * 80)
        print("INSCRIBIENDO PAREJAS")
        print("=" * 80)
        
        for i, (j1, j2, restricciones) in enumerate(PAREJAS, 1):
            # Resolver IDs
            id1 = nuevos_ids[j1] if isinstance(j1, str) else j1
            id2 = nuevos_ids[j2] if isinstance(j2, str) else j2
            
            # Obtener nombres
            u1 = conn.execute(text("SELECT nombre_usuario FROM usuarios WHERE id_usuario = :id"), {"id": id1}).fetchone()
            u2 = conn.execute(text("SELECT nombre_usuario FROM usuarios WHERE id_usuario = :id"), {"id": id2}).fetchone()
            
            nombre_pareja = f"{u1[0]} + {u2[0]}"
            
            # Verificar si ya existe la pareja
            existe = conn.execute(text("""
                SELECT id FROM torneos_parejas
                WHERE torneo_id = :tid AND categoria_id = :cid
                  AND ((jugador1_id = :j1 AND jugador2_id = :j2) OR (jugador1_id = :j2 AND jugador2_id = :j1))
            """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID, "j1": id1, "j2": id2}).fetchone()
            
            if existe:
                print(f"⚠️  Pareja {i} ya existe (ID: {existe[0]})")
                pareja_id = existe[0]
            else:
                # Crear pareja con restricciones en formato JSON
                import json
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
            
            # Las restricciones ya están en disponibilidad_horaria (JSON), no usar tabla separada
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ INSCRIPCIÓN COMPLETADA")
        print("=" * 80)
        
        # Verificar parejas inscritas
        parejas = conn.execute(text("""
            SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :tid AND categoria_id = :cid
        """), {"tid": TORNEO_ID, "cid": CATEGORIA_ID}).fetchone()
        
        print(f"Total parejas en 7ma: {parejas[0]}")

if __name__ == "__main__":
    main()
