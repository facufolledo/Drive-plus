import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TORNEO_ID = 45
SABADO = "2026-03-07"

def buscar_usuario(s, nombre, apellido):
    """Busca un usuario por nombre y apellido"""
    result = s.execute(text("""
        SELECT u.id_usuario, pu.nombre, pu.apellido
        FROM usuarios u
        JOIN perfil_usuarios pu ON u.id_usuario = pu.id_usuario
        WHERE LOWER(pu.nombre) LIKE LOWER(:nombre) 
        AND LOWER(pu.apellido) LIKE LOWER(:apellido)
        LIMIT 1
    """), {"nombre": f"%{nombre}%", "apellido": f"%{apellido}%"}).fetchone()
    
    return result

def crear_usuario(s, nombre, apellido):
    """Crea un usuario nuevo"""
    username = f"{nombre.lower()}{apellido.lower()}".replace(" ", "")
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

def main():
    s = Session()
    try:
        print("=" * 80)
        print("FIX PARTIDO 1017 - ZONA H")
        print("=" * 80)
        
        # Buscar o crear Juan Loto
        juan_loto = buscar_usuario(s, "Juan", "Loto")
        if not juan_loto:
            print("\n📝 Creando Juan Loto...")
            juan_loto_id = crear_usuario(s, "Juan", "Loto")
        else:
            juan_loto_id = juan_loto[0]
            print(f"\n✅ Juan Loto encontrado (ID: {juan_loto_id})")
        
        # Buscar o crear Emanuel Reyes
        emanuel_reyes = buscar_usuario(s, "Emanuel", "Reyes")
        if not emanuel_reyes:
            print("\n📝 Creando Emanuel Reyes...")
            emanuel_reyes_id = crear_usuario(s, "Emanuel", "Reyes")
        else:
            emanuel_reyes_id = emanuel_reyes[0]
            print(f"✅ Emanuel Reyes encontrado (ID: {emanuel_reyes_id})")
        
        # Obtener zona H de 4ta
        zona_h = s.execute(text("""
            SELECT tz.id
            FROM torneo_zonas tz
            JOIN torneo_categorias tc ON tz.categoria_id = tc.id
            WHERE tc.torneo_id = :tid AND tc.nombre = '4ta' AND tz.nombre = 'Zona H'
        """), {"tid": TORNEO_ID}).scalar()
        
        if not zona_h:
            print("\n❌ Zona H no encontrada")
            return
        
        print(f"\n✅ Zona H encontrada (ID: {zona_h})")
        
        # Crear nueva pareja correcta
        print(f"\n📝 Creando pareja correcta: Juan Loto / Emanuel Reyes...")
        s.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, jugador1_id, jugador2_id)
            VALUES (:tid, :j1, :j2)
        """), {"tid": TORNEO_ID, "j1": juan_loto_id, "j2": emanuel_reyes_id})
        
        nueva_pareja_id = s.execute(text("""
            SELECT id FROM torneos_parejas 
            WHERE torneo_id = :tid AND jugador1_id = :j1 AND jugador2_id = :j2
            ORDER BY id DESC LIMIT 1
        """), {"tid": TORNEO_ID, "j1": juan_loto_id, "j2": emanuel_reyes_id}).scalar()
        
        print(f"✅ Nueva pareja creada (ID: {nueva_pareja_id})")
        
        # Inscribir en zona
        s.execute(text("""
            INSERT INTO torneo_zona_parejas (zona_id, pareja_id)
            VALUES (:zid, :pid)
        """), {"zid": zona_h, "pid": nueva_pareja_id})
        
        print("✅ Pareja inscrita en Zona H")
        
        # Actualizar partido 1017
        print(f"\n📝 Actualizando partido 1017...")
        
        s.execute(text("""
            UPDATE partidos
            SET pareja2_id = :nueva_pareja,
                fecha_hora = :fecha_hora,
                fecha = :fecha,
                cancha_id = 91
            WHERE id_partido = 1017
        """), {
            "nueva_pareja": nueva_pareja_id,
            "fecha_hora": f"{SABADO} 12:00:00",
            "fecha": SABADO
        })
        
        print("✅ Partido 1017 actualizado")
        
        # Ahora eliminar pareja incorrecta (992)
        print(f"\n🗑️  Eliminando pareja incorrecta (ID: 992)...")
        
        # Eliminar relación zona-pareja
        s.execute(text("""
            DELETE FROM torneo_zona_parejas WHERE pareja_id = 992
        """))
        
        # Eliminar pareja
        s.execute(text("""
            DELETE FROM torneos_parejas WHERE id = 992
        """))
        
        print("✅ Pareja incorrecta eliminada")
        
        s.commit()
        
        print("\n" + "=" * 80)
        print("✅ PARTIDO 1017 CORREGIDO EXITOSAMENTE")
        print("=" * 80)
        print("  Agustín Aguirre / Brian Barrera vs Juan Loto / Emanuel Reyes")
        print("  Sábado 12:00, Cancha 3")
        
    except Exception as e:
        s.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        s.close()

if __name__ == "__main__":
    main()
