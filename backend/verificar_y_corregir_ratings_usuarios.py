"""
Script para verificar y corregir ratings de usuarios
Calcula el rating esperado basado en:
1. Rating inicial según categoría
2. Suma de todos los deltas del historial_rating
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL no encontrada")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Rangos de categorías
RANGOS_CATEGORIAS = {
    'Principiante': 249,
    '8va': 749,
    '7ma': 1099,
    '6ta': 1299,
    '5ta': 1499,
    '4ta': 1699,
    '3ra': 1899
}

def obtener_categoria_inicial(usuario_id):
    """Obtiene la categoría con la que empezó el usuario"""
    query = text("""
        SELECT c.nombre
        FROM usuarios u
        LEFT JOIN categorias c ON u.id_categoria = c.id_categoria
        WHERE u.id_usuario = :user_id
    """)
    result = session.execute(query, {"user_id": usuario_id}).fetchone()
    
    if result and result[0]:
        return result[0]
    
    # Si no tiene categoría asignada, buscar en el primer partido
    query_primer_partido = text("""
        SELECT p.categoria
        FROM partidos p
        JOIN partido_jugadores pj ON p.id_partido = pj.id_partido
        WHERE pj.id_usuario = :user_id
        ORDER BY p.fecha ASC
        LIMIT 1
    """)
    result = session.execute(query_primer_partido, {"user_id": usuario_id}).fetchone()
    
    if result and result[0]:
        return result[0]
    
    return None

def verificar_usuario(nombre, apellido):
    """Verifica el rating de un usuario específico"""
    # Buscar usuario
    query = text("""
        SELECT u.id_usuario, u.rating, p.nombre, p.apellido
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE LOWER(p.nombre) = LOWER(:nombre) 
        AND LOWER(p.apellido) = LOWER(:apellido)
    """)
    
    result = session.execute(query, {"nombre": nombre, "apellido": apellido}).fetchone()
    
    if not result:
        print(f"❌ Usuario no encontrado: {nombre} {apellido}")
        return None
    
    user_id, rating_actual, nombre_real, apellido_real = result
    print(f"\n{'='*80}")
    print(f"👤 Usuario: {nombre_real} {apellido_real} (ID: {user_id})")
    print(f"📊 Rating actual en BD: {rating_actual}")
    
    # Obtener categoría inicial
    categoria_inicial = obtener_categoria_inicial(user_id)
    if not categoria_inicial:
        print("⚠️  No se pudo determinar la categoría inicial")
        return None
    
    rating_inicial = RANGOS_CATEGORIAS.get(categoria_inicial)
    if not rating_inicial:
        print(f"⚠️  Categoría inicial desconocida: {categoria_inicial}")
        return None
    
    print(f"🎯 Categoría inicial: {categoria_inicial}")
    print(f"🎯 Rating inicial: {rating_inicial}")
    
    # Obtener todos los deltas del historial
    query_deltas = text("""
        SELECT h.id_partido, h.delta, h.rating_antes, h.rating_despues, p.fecha
        FROM historial_rating h
        JOIN partidos p ON h.id_partido = p.id_partido
        WHERE h.id_usuario = :user_id
        ORDER BY p.fecha ASC
    """)
    
    deltas = session.execute(query_deltas, {"user_id": user_id}).fetchall()
    
    if not deltas:
        print("⚠️  No hay historial de rating")
        return None
    
    print(f"\n📈 Historial de partidos ({len(deltas)} partidos):")
    print(f"{'Partido':<10} {'Delta':<8} {'Antes':<8} {'Después':<10} {'Fecha'}")
    print("-" * 80)
    
    suma_deltas = 0
    for partido_id, delta, antes, despues, fecha in deltas:
        suma_deltas += delta
        print(f"{partido_id:<10} {delta:+8} {antes:<8} {despues:<10} {fecha}")
    
    rating_esperado = rating_inicial + suma_deltas
    diferencia = rating_actual - rating_esperado
    
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN:")
    print(f"   Rating inicial:   {rating_inicial}")
    print(f"   Suma de deltas:   {suma_deltas:+d}")
    print(f"   Rating esperado:  {rating_esperado}")
    print(f"   Rating actual:    {rating_actual}")
    print(f"   Diferencia:       {diferencia:+d}")
    
    if diferencia != 0:
        print(f"\n⚠️  HAY UNA DISCREPANCIA DE {abs(diferencia)} PUNTOS")
        return {
            'user_id': user_id,
            'nombre': nombre_real,
            'apellido': apellido_real,
            'rating_actual': rating_actual,
            'rating_esperado': rating_esperado,
            'diferencia': diferencia
        }
    else:
        print(f"\n✅ Rating correcto")
        return None

def corregir_rating(user_id, rating_correcto):
    """Corrige el rating de un usuario"""
    query = text("""
        UPDATE usuarios
        SET rating = :rating
        WHERE id_usuario = :user_id
    """)
    
    session.execute(query, {"rating": rating_correcto, "user_id": user_id})
    session.commit()
    print(f"✅ Rating corregido para usuario {user_id}")

def verificar_todos_usuarios():
    """Verifica todos los usuarios que tienen partidos"""
    query = text("""
        SELECT DISTINCT u.id_usuario, p.nombre, p.apellido, u.rating
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN partido_jugadores pj ON u.id_usuario = pj.id_usuario
        ORDER BY p.apellido, p.nombre
    """)
    
    usuarios = session.execute(query).fetchall()
    
    print(f"\n🔍 Verificando {len(usuarios)} usuarios con partidos...\n")
    
    usuarios_con_error = []
    
    for user_id, nombre, apellido, rating_actual in usuarios:
        resultado = verificar_usuario(nombre, apellido)
        if resultado:
            usuarios_con_error.append(resultado)
    
    if usuarios_con_error:
        print(f"\n{'='*80}")
        print(f"⚠️  USUARIOS CON DISCREPANCIAS ({len(usuarios_con_error)}):")
        print(f"{'='*80}")
        for u in usuarios_con_error:
            print(f"{u['nombre']} {u['apellido']}: {u['rating_actual']} → {u['rating_esperado']} (diferencia: {u['diferencia']:+d})")
        
        respuesta = input(f"\n¿Corregir los {len(usuarios_con_error)} usuarios? (s/n): ")
        if respuesta.lower() == 's':
            for u in usuarios_con_error:
                corregir_rating(u['user_id'], u['rating_esperado'])
            print(f"\n✅ {len(usuarios_con_error)} usuarios corregidos")
    else:
        print(f"\n✅ Todos los usuarios tienen ratings correctos")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2:
        # Verificar usuario específico
        nombre = sys.argv[1]
        apellido = sys.argv[2]
        resultado = verificar_usuario(nombre, apellido)
        
        if resultado:
            respuesta = input(f"\n¿Corregir rating de {resultado['rating_actual']} a {resultado['rating_esperado']}? (s/n): ")
            if respuesta.lower() == 's':
                corregir_rating(resultado['user_id'], resultado['rating_esperado'])
    else:
        # Verificar todos los usuarios
        verificar_todos_usuarios()
    
    session.close()
