import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno
load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL no encontrada")
    exit(1)

# Crear engine y sesión
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Buscar tu usuario (facufolledo7)
    result = session.execute(text("""
        SELECT 
            u.id_usuario,
            u.nombre_usuario,
            u.email,
            u.es_administrador,
            u.puede_crear_torneos,
            p.nombre,
            p.apellido
        FROM usuarios u
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE u.nombre_usuario = 'facufolledo7'
    """))
    
    usuario = result.fetchone()
    
    if usuario:
        print("✅ Usuario encontrado:")
        print(f"   ID: {usuario[0]}")
        print(f"   Username: {usuario[1]}")
        print(f"   Email: {usuario[2]}")
        print(f"   Es Administrador: {usuario[3]}")
        print(f"   Puede Crear Torneos: {usuario[4]}")
        print(f"   Nombre: {usuario[5]} {usuario[6]}")
        
        if not usuario[3]:
            print("\n⚠️  El usuario NO es administrador")
            print("   Para activar admin, ejecuta:")
            print(f"   UPDATE usuarios SET es_administrador = true WHERE id_usuario = {usuario[0]};")
    else:
        print("❌ Usuario 'facufolledo7' no encontrado")
        
        # Buscar otros usuarios admin
        result = session.execute(text("""
            SELECT 
                u.id_usuario,
                u.nombre_usuario,
                u.email,
                u.es_administrador
            FROM usuarios u
            WHERE u.es_administrador = true
        """))
        
        admins = result.fetchall()
        if admins:
            print("\n✅ Usuarios administradores encontrados:")
            for admin in admins:
                print(f"   - {admin[1]} (ID: {admin[0]}, Email: {admin[2]})")
        else:
            print("\n⚠️  No hay usuarios administradores en la base de datos")

finally:
    session.close()
