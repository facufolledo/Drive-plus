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
CATEGORIA_NOMBRE = "8va"
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
        print("CREAR FIXTURE 8VA - TORNEO 45")
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
        
        p1 = crear_pareja(s, "ALFARO", "AXEL", "VELAZQUE", "JUAN", zona_a)
        p2 = crear_pareja(s, "VILLANOVA", "IGNACIO", "FERNANDEZ", "FACUNDO", zona_a)
        p3 = crear_pareja(s, "ALMADA", "LUCAS", "MEDINA", "JORGE", zona_a)
        
        crear_partido(s, p1, p2, zona_a, cat_id, VIERNES, "22:00", 3)
        crear_partido(s, p2, p3, zona_a, cat_id, VIERNES, "15:00", 3)
        crear_partido(s, p3, p1, zona_a, cat_id, JUEVES, "15:00", 1)
        
        # ZONA B
        print("\n📍 Creando Zona B...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona B', 2)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_b = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona B'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "ALFARO", "BENJA", "MANRIQUE", "FEDERICO", zona_b)
        p2 = crear_pareja(s, "OLIVERA", "LUCAS", "GREGORI", "LUCAS", zona_b)
        p3 = crear_pareja(s, "BARRO", "MAXIMILIANO", "BARROS", "RODRIGO", zona_b)
        
        crear_partido(s, p1, p2, zona_b, cat_id, JUEVES, "20:00", 3)
        crear_partido(s, p2, p3, zona_b, cat_id, VIERNES, "20:00", 3)
        crear_partido(s, p3, p1, zona_b, cat_id, VIERNES, "23:00", 3)
        
        # ZONA C
        print("\n📍 Creando Zona C...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona C', 3)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_c = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona C'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "COLINA", "JEREMIAS", "COLINA", "FRANCO", zona_c)
        p2 = crear_pareja(s, "BRITOS", "MAXI", "SALAS", "NANO", zona_c)
        p3 = crear_pareja(s, "TOLEDO", "LEANDRO", "TRAMONTIN", "MATIAS", zona_c)
        
        crear_partido(s, p1, p2, zona_c, cat_id, JUEVES, "20:00", 2)
        crear_partido(s, p2, p3, zona_c, cat_id, VIERNES, "23:00", 1)
        crear_partido(s, p3, p1, zona_c, cat_id, JUEVES, "23:00", 3)
        
        # ZONA D
        print("\n📍 Creando Zona D...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona D', 4)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_d = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona D'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "BRIZUELA", "MARTIN", "CEBALLO", "SANTIAGO", zona_d)
        p2 = crear_pareja(s, "CORTEZ", "AGUSTIN", "AGUILAR", "AGUSTIN", zona_d)
        p3 = crear_pareja(s, "LUNA", "LEONARDO", "BORIS", "NIETO", zona_d)
        
        crear_partido(s, p1, p2, zona_d, cat_id, JUEVES, "22:00", 1)
        crear_partido(s, p2, p3, zona_d, cat_id, VIERNES, "01:00", 2)
        crear_partido(s, p3, p1, zona_d, cat_id, SABADO, "13:00", 2)
        
        # ZONA E
        print("\n📍 Creando Zona E...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona E', 5)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_e = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona E'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "CALDERON", "ARIEL", "VERA", "JERE", zona_e)
        p2 = crear_pareja(s, "CARDENAS", "TOBIAS", "ROJAS", "AGUSTIN", zona_e)
        p3 = crear_pareja(s, "DIOGENES", "MIRANDA", "DIAMANTE", "BAUTISTA", zona_e)
        
        crear_partido(s, p1, p2, zona_e, cat_id, JUEVES, "20:00", 1)
        crear_partido(s, p2, p3, zona_e, cat_id, JUEVES, "16:00", 3)
        crear_partido(s, p3, p1, zona_e, cat_id, VIERNES, "19:00", 3)
        
        # ZONA F (2 parejas)
        print("\n📍 Creando Zona F...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona F', 6)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_f = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona F'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "ZARACHO", "", "MERCADO", "CHILECITO", zona_f)
        p2 = crear_pareja(s, "ESTEVEZ", "ROGELIO", "OROPEL", "BRAIAN", zona_f)
        
        crear_partido(s, p1, p2, zona_f, cat_id, SABADO, "10:00", 2)
        
        # ZONA G (2 parejas)
        print("\n📍 Creando Zona G...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona G', 7)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_g = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona G'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "GONZALEZ", "JEREMIAS", "IMANOL", "MORALES", zona_g)
        p2 = crear_pareja(s, "FUENTES", "MARTIN", "VILLAGRAN", "JULIAN", zona_g)
        
        crear_partido(s, p1, p2, zona_g, cat_id, JUEVES, "23:59", 1)  # 00:00 → 23:59
        
        # ZONA H (2 parejas)
        print("\n📍 Creando Zona H...")
        s.execute(text("""
            INSERT INTO torneo_zonas (torneo_id, categoria_id, nombre, numero_orden)
            VALUES (:tid, :cid, 'Zona H', 8)
        """), {"tid": TORNEO_ID, "cid": cat_id})
        zona_h = s.execute(text("SELECT id FROM torneo_zonas WHERE categoria_id = :cid AND nombre = 'Zona H'"), 
                          {"cid": cat_id}).scalar()
        
        p1 = crear_pareja(s, "FERNANDEZ", "CARLOS", "MENA", "LEO", zona_h)
        p2 = crear_pareja(s, "FERREYRA", "", "LUNA", "", zona_h)
        
        crear_partido(s, p1, p2, zona_h, cat_id, JUEVES, "16:00", 1)
        
        s.commit()
        
        print("\n" + "=" * 80)
        print("✅ FIXTURE 8VA CREADO EXITOSAMENTE")
        print("=" * 80)
        print(f"Total: 8 zonas, 18 partidos")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
