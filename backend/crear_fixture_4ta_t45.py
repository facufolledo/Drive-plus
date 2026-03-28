import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45
CATEGORIA_NOMBRE = "4ta"
ID_CREADOR = 1

# IDs de canchas
CANCHAS = {1: 89, 2: 90, 3: 91}

# Fechas base del torneo
JUEVES = "2026-03-05"
VIERNES = "2026-03-06"
SABADO = "2026-03-07"

def buscar_o_crear_usuario(s, nombre, apellido):
    """Busca un usuario por nombre y apellido, si no existe lo crea"""
    result = s.execute(text("""
        SELECT id_usuario FROM usuarios 
        WHERE LOWER(nombre_usuario) = LOWER(:nombre) 
        OR (LOWER(nombre_usuario) LIKE LOWER(:busqueda))
        LIMIT 1
    """), {"nombre": f"{nombre}{apellido}", "busqueda": f"%{nombre}%{apellido}%"}).fetchone()
    
    if result:
        return result[0]
    
    # Crear usuario nuevo
    username = f"{nombre.lower()}{apellido.lower()}"
    s.execute(text("""
        INSERT INTO usuarios (nombre_usuario, email, password_hash)
        VALUES (:username, :email, 'temp_hash')
    """), {"username": username, "email": f"{username}@temp.com"})
    
    user_id = s.execute(text("SELECT id_usuario FROM usuarios WHERE nombre_usuario = :username"), 
                        {"username": username}).scalar()
    
    # Crear perfil
    s.execute(text("""
        INSERT INTO perfil_usuarios (id_usuario, nombre, apellido)
        VALUES (:uid, :nombre, :apellido)
    """), {"uid": user_id, "nombre": nombre, "apellido": apellido})
    
    print(f"  ✅ Creado usuario: {nombre} {apellido} (ID: {user_id})")
    return user_id

def crear_pareja(s, j1_nombre, j1_apellido, j2_nombre, j2_apellido, zona_id):
    """Crea una pareja e inscribe en la zona"""
    j1_id = buscar_o_crear_usuario(s, j1_nombre, j1_apellido)
    j2_id = buscar_o_crear_usuario(s, j2_nombre, j2_apellido)
    
    # Crear pareja
    s.execute(text("""
        INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id)
        VALUES (:tid, :j1, :j2)
    """), {"tid": TORNEO_ID, "j1": j1_id, "j2": j2_id})
    
    pareja_id = s.execute(text("""
        SELECT id FROM torneos_parejas 
        WHERE torneo_id = :tid AND jugador1_id = :j1 AND jugador2_id = :j2
        ORDER BY id DESC LIMIT 1
    """), {"tid": TORNEO_ID, "j1": j1_id, "j2": j2_id}).scalar()
    
    # Inscribir en zona
    s.execute(text("""
        INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
        VALUES (:zid, :pid)
    """), {"zid": zona_id, "pid": pareja_id})
    
    return pareja_id

def crear_partido(s, pareja1_id, pareja2_id, zona_id, categoria_id, dia, hora, cancha_num):
    """Crea un partido"""
    cancha_id = CANCHAS[cancha_num]
    fecha_hora = f"{dia} {hora}:00"
    
    s.execute(text("""
        INSERT INTO partidos (
            id_torneo, categoria_id, pareja1_id, pareja2_id, zona_id,
            fecha_hora, fecha, cancha_id, estado, id_creador
        ) VALUES (
            :tid, :cid, :p1, :p2, :zid,
            :fh, :f, :cancha, 'pendiente', :creador
        )
    """), {
        "tid": TORNEO_ID, "cid": categoria_id, "p1": pareja1_id, "p2": pareja2_id,
        "zid": zona_id, "fh": fecha_hora, "f": dia, "cancha": cancha_id, "creador": ID_CREADOR
    })

def main():
    s = Session()
    try:
        print("=" * 80)
        print("CREAR FIXTURE 4TA - TORNEO 45")
        print("=" * 80)
        
        # Obtener categoria_id
        cat_id = s.execute(text("""
            SELECT id FROM torneo_categorias 
            WHERE torneo_id = :tid AND nombre = :nombre
        """), {"tid": TORNEO_ID, "nombre": CATEGORIA_NOMBRE}).scalar()
        
        if not cat_id:
            print(f"❌ No se encontró la categoría {CATEGORIA_NOMBRE}")
            return
        
        print(f"\n✅ Categoría {CATEGORIA_NOMBRE} encontrada (ID: {cat_id})")
        
        # ZONA A
        print("\n📍 Creando Zona A...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona A', 1)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_a = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona A'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "MILLICAY", "", "TELLO", "", zona_a)
        p2 = crear_pareja(s, "MATIA", "OLIVERA", "JOFRE", "RAMIRO", zona_a)
        p3 = crear_pareja(s, "SILVA", "SERGIO", "RODRIGUEZ", "LUIS", zona_a)
        
        crear_partido(s, p1, p2, zona_a, cat_id, JUEVES, "15:00", 2)
        crear_partido(s, p2, p3, zona_a, cat_id, JUEVES, "01:00", 3)
        crear_partido(s, p3, p1, zona_a, cat_id, SABADO, "16:00", 2)
        
        # ZONA B
        print("\n📍 Creando Zona B...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona B', 2)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_b = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona B'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "MERLO", "", "MERLO", "", zona_b)
        p2 = crear_pareja(s, "GASTON", "ROMER", "ISMAEL", "BALLEJO", zona_b)
        p3 = crear_pareja(s, "MONTIVERO", "JUAN FELIPE", "JUAN", "CRUZ", zona_b)
        
        crear_partido(s, p1, p2, zona_b, cat_id, VIERNES, "15:00", 2)
        crear_partido(s, p2, p3, zona_b, cat_id, VIERNES, "18:00", 2)
        crear_partido(s, p3, p1, zona_b, cat_id, SABADO, "11:00", 2)
        
        # ZONA C
        print("\n📍 Creando Zona C...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona C', 3)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_c = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona C'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "FARRAN", "BASTIAN", "MALDONADO", "ALEXIS", zona_c)
        p2 = crear_pareja(s, "DIAZ", "MATEO", "SOSA", "BAUTI", zona_c)
        p3 = crear_pareja(s, "BRIZUELA", "ALVARO", "CHUMBITA", "AGUSTIN", zona_c)
        
        crear_partido(s, p1, p2, zona_c, cat_id, JUEVES, "16:00", 3)
        crear_partido(s, p2, p3, zona_c, cat_id, VIERNES, "17:00", 1)
        crear_partido(s, p3, p1, zona_c, cat_id, VIERNES, "22:00", 1)
        
        # ZONA D
        print("\n📍 Creando Zona D...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona D', 4)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_d = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona D'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "FIGUEROA", "", "GOMEZ", "", zona_d)
        p2 = crear_pareja(s, "ARREBOLA", "JERE", "BURGONE", "", zona_d)
        p3 = crear_pareja(s, "VILLEGAS", "NACHO", "GAITAN", "MATIAS", zona_d)
        
        crear_partido(s, p1, p2, zona_d, cat_id, VIERNES, "21:00", 1)
        crear_partido(s, p2, p3, zona_d, cat_id, VIERNES, "18:00", 1)
        crear_partido(s, p3, p1, zona_d, cat_id, SABADO, "11:00", 3)
        
        # ZONA E
        print("\n📍 Creando Zona E...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona E', 5)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_e = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona E'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "COPPEDE", "", "", "", zona_e)
        p2 = crear_pareja(s, "VERGARA", "JOAQUIN", "FUENTES", "RICARDO", zona_e)
        p3 = crear_pareja(s, "LIGORRIA", "", "BRIZUELA", "", zona_e)
        
        crear_partido(s, p1, p2, zona_e, cat_id, VIERNES, "21:00", 2)
        crear_partido(s, p2, p3, zona_e, cat_id, SABADO, "11:00", 1)
        crear_partido(s, p3, p1, zona_e, cat_id, SABADO, "15:00", 2)
        
        # ZONA F
        print("\n📍 Creando Zona F...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona F', 6)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_f = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona F'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "NIETO", "AXEL", "GOMEZ", "MATEO", zona_f)
        p2 = crear_pareja(s, "ELIZONDO", "GERONIMO", "CHAVEZ", "DANIEL", zona_f)
        p3 = crear_pareja(s, "AGÜERO", "ALE", "LOIS", "HOGA", zona_f)
        
        crear_partido(s, p1, p2, zona_f, cat_id, VIERNES, "19:00", 2)
        crear_partido(s, p2, p3, zona_f, cat_id, SABADO, "12:00", 2)
        crear_partido(s, p3, p1, zona_f, cat_id, SABADO, "14:00", 2)
        
        # ZONA G (2 parejas)
        print("\n📍 Creando Zona G...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona G', 7)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_g = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona G'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "BESTANI", "SEBASTIAN", "GAVIO", "CARLOS", zona_g)
        p2 = crear_pareja(s, "HERRERA", "NICOLAS", "ORELLANO", "KEVIN", zona_g)
        
        crear_partido(s, p1, p2, zona_g, cat_id, SABADO, "14:00", 3)
        
        # ZONA H (2 parejas)
        print("\n📍 Creando Zona H...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona H', 8)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_h = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona H'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "AGUIRRE", "AGUSTIN", "BRAIAN", "BARRERA", zona_h)
        p2 = crear_pareja(s, "ALAN", "CORONAS", "", "", zona_h)
        
        crear_partido(s, p1, p2, zona_h, cat_id, JUEVES, "16:00", 2)
        
        # ZONA I (3 parejas)
        print("\n📍 Creando Zona I...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona I', 9)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_i = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona I'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "JAIN", "FACUNDO", "FARRUCO", "", zona_i)
        p2 = crear_pareja(s, "JUAN", "MAGUI", "MATEO", "GARCIA", zona_i)
        p3 = crear_pareja(s, "QUIPILDOR", "", "LIONEL", "", zona_i)
        
        crear_partido(s, p1, p2, zona_i, cat_id, JUEVES, "17:00", 2)
        crear_partido(s, p2, p3, zona_i, cat_id, VIERNES, "19:00", 2)
        crear_partido(s, p3, p1, zona_i, cat_id, JUEVES, "19:00", 2)
        
        # ZONA J (2 parejas)
        print("\n📍 Creando Zona J...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona J', 10)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_j = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona J'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "DEL FRANCO", "THIAGO", "RIVERO", "JOAQUIN", zona_j)
        p2 = crear_pareja(s, "CORONA", "ALAN", "", "", zona_j)
        
        crear_partido(s, p1, p2, zona_j, cat_id, SABADO, "10:00", 2)
        
        s.commit()
        
        print("\n" + "=" * 80)
        print("✅ FIXTURE 4TA CREADO EXITOSAMENTE")
        print("=" * 80)
        print(f"Total: 10 zonas, 22 partidos")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
