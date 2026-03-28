"""
Inscribir parejas en categoría 5ta del torneo 46
IMPORTANTE: Las restricciones son horarios NO disponibles
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

# Jugadores que NO existen (crear como temp)
NUEVOS_JUGADORES = [
    {"nombre": "Julián", "apellido": "Bustamante", "username": "julian.bustamante.t46"},
    {"nombre": "Juan Pablo", "apellido": "Lobato", "username": "juanpablo.lobato.t46"},
    {"nombre": "Mario", "apellido": "Santander", "username": "mario.santander.t46"},
    {"nombre": "Cristofer", "apellido": "Galleguillo", "username": "cristofer.galleguillo.t46"},
    {"nombre": "Horacio", "apellido": "Escalante", "username": "horacio.escalante.t46"},
    {"nombre": "Luciano", "apellido": "Paez", "username": "luciano.paez.t46"},
    {"nombre": "Juan", "apellido": "Córdoba", "username": "juan.cordoba.t46"},
    {"nombre": "Matías", "apellido": "Carrizo", "username": "matias.carrizo.t46"},
    {"nombre": "Miguel", "apellido": "Estrada", "username": "miguel.estrada.t46"},
    {"nombre": "Tomas", "apellido": "Carrizo", "username": "tomas.carrizo.t46"},
    {"nombre": "Joaquin", "apellido": "Mercado", "username": "joaquin.mercado.t46"},
    {"nombre": "Cristian", "apellido": "Gurgone", "username": "cristian.gurgone.t46"},
    {"nombre": "Nacho", "apellido": "Olima", "username": "nacho.olima.t46"},
]

# Parejas: (j1, j2, restricciones_NO_disponibles)
# IDs confirmados: Lobos 41, Aguilar Gonzalo 587, Castro Joel 586, Nani 31, Abrego 590,
# Oliva Bautista 200, Farran 240, Montiel 1024, Calderón 201, Facu Martín 581, 
# Samir Pablo 498, Palacios 230, Navarro 602, Loto 603, Reyes 553
PAREJAS = [
    # P1: Bustamante + Lobato - viernes +21 (NO disponible antes de 21)
    ("julian.bustamante.t46", "juanpablo.lobato.t46",
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "21:00"}]),
    
    # P2: Lobos + Santander - viernes +20 (NO disponible antes de 20)
    (41, "mario.santander.t46",
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "20:00"}]),
    
    # P3: Aguilar Gonzalo + Galleguillo - viernes +14 (NO disponible antes de 14)
    (587, "cristofer.galleguillo.t46",
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "14:00"}]),
    
    # P4: Escalante + Castro - viernes +21, sábado +13 (NO disponible antes de esas horas)
    ("horacio.escalante.t46", 586,
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "21:00"},
      {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "13:00"}]),
    
    # P5: Paez + Córdoba - viernes +16 -20 (disponible 16-20, NO disponible resto)
    ("luciano.paez.t46", "juan.cordoba.t46",
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "16:00"},
      {"dias": ["viernes"], "horaInicio": "20:00", "horaFin": "23:59"}]),
    
    # P6: Carrizo Matías + Estrada - viernes +18 (NO disponible antes de 18)
    ("matias.carrizo.t46", "miguel.estrada.t46",
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "18:00"}]),
    
    # P7: Nani + Abrego - viernes +19 (NO disponible antes de 19)
    (31, 590,
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "19:00"}]),
    
    # P8: Carrizo Tomas + Oliva - viernes +14 menos 18 +22 (disponible 14-18 y después 22)
    ("tomas.carrizo.t46", 200,
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "14:00"},
      {"dias": ["viernes"], "horaInicio": "18:00", "horaFin": "22:00"}]),
    
    # P9: Farran + Montiel - viernes +14 (NO disponible antes de 14)
    (240, 1024,
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "14:00"}]),
    
    # P10: Mercado + Calderón - viernes +20 menos 23, sábado +16 (disponible 20-23 viernes, después 16 sábado)
    ("joaquin.mercado.t46", 201,
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "20:00"},
      {"dias": ["viernes"], "horaInicio": "23:00", "horaFin": "23:59"},
      {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "16:00"}]),
    
    # P11: Facu Martín + Samir - viernes +14 -19 (disponible 14-19)
    (581, 498,
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "14:00"},
      {"dias": ["viernes"], "horaInicio": "19:00", "horaFin": "23:59"}]),
    
    # P12: Palacios + Gurgone - viernes 18 y 21 (disponible entre 18-21)
    (230, "cristian.gurgone.t46",
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "18:00"},
      {"dias": ["viernes"], "horaInicio": "21:00", "horaFin": "23:59"}]),
    
    # P13: Navarro + Loto - sábado +14 (NO disponible antes de 14 sábado)
    (602, 603,
     [{"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "14:00"}]),
    
    # P14: Reyes + Olima - viernes +20, sábado +16 (NO disponible antes de esas horas)
    (553, "nacho.olima.t46",
     [{"dias": ["viernes"], "horaInicio": "00:00", "horaFin": "20:00"},
      {"dias": ["sabado"], "horaInicio": "00:00", "horaFin": "16:00"}]),
]

def main():
    print("=" * 80)
    print(f"INSCRIPCIÓN TORNEO {TORNEO_ID} - 5TA")
    print("=" * 80)
    
    with engine.connect() as conn:
        # 1. Verificar torneo
        torneo = conn.execute(text("SELECT id, nombre FROM torneos WHERE id = :tid"), {"tid": TORNEO_ID}).fetchone()
        if not torneo:
            print(f"❌ ERROR: Torneo {TORNEO_ID} no encontrado")
            return
        print(f"✅ Torneo: {torneo.nombre}")
        
        # 2. Obtener categoria_id de torneo_categorias
        cat = conn.execute(text("""
            SELECT id FROM torneo_categorias WHERE torneo_id = :tid AND nombre = '5ta'
        """), {"tid": TORNEO_ID}).fetchone()
        
        if not cat:
            print("❌ ERROR: Categoría 5ta no encontrada en el torneo")
            return
        CATEGORIA_ID = cat.id
        print(f"✅ Categoría 5ta del torneo: ID {CATEGORIA_ID}")
        
        # 3. Obtener id_categoria general
        cat_general = conn.execute(text("SELECT id_categoria FROM categorias WHERE nombre = '5ta'")).fetchone()
        if not cat_general:
            print("❌ ERROR: Categoría 5ta no encontrada en categorias generales")
            return
        CATEGORIA_GENERAL_ID = cat_general.id_categoria
        print(f"✅ Categoría 5ta general: ID {CATEGORIA_GENERAL_ID}")
        
        # 4. Crear usuarios nuevos
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
        
        # 5. Inscribir parejas
        print("\n" + "=" * 80)
        print("INSCRIBIENDO PAREJAS")
        print("=" * 80)
        
        for i, (j1, j2, restricciones) in enumerate(PAREJAS, 1):
            id1 = nuevos_ids[j1] if isinstance(j1, str) else j1
            id2 = nuevos_ids[j2] if isinstance(j2, str) else j2
            
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
        
        print(f"Total parejas en 5ta: {total[0]}")

if __name__ == "__main__":
    main()
