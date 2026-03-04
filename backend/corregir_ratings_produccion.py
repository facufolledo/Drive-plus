"""
Script para verificar y corregir ratings en PRODUCCIÓN
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno de PRODUCCIÓN
load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL no encontrada en .env.production")
    sys.exit(1)

print(f"🔗 Conectando a: {DATABASE_URL[:50]}...")

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

def verificar_y_corregir_todos():
    """Verifica y corrige todos los usuarios automáticamente"""
    # Obtener todos los usuarios con partidos (sin filtrar por historial_rating)
    query = text("""
        SELECT DISTINCT u.id_usuario, p.nombre, p.apellido, u.rating
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        JOIN partido_jugadores pj ON u.id_usuario = pj.id_usuario
        ORDER BY p.apellido, p.nombre
    """)
    
    usuarios = session.execute(query).fetchall()
    
    print(f"\n🔍 Verificando {len(usuarios)} usuarios con partidos en PRODUCCIÓN...\n")
    print(f"{'='*100}")
    
    usuarios_corregidos = []
    usuarios_correctos = []
    usuarios_sin_categoria = []
    
    for user_id, nombre, apellido, rating_actual in usuarios:
        # Obtener categoría inicial
        categoria_inicial = obtener_categoria_inicial(user_id)
        if not categoria_inicial:
            usuarios_sin_categoria.append(f"{nombre} {apellido} (ID: {user_id})")
            continue
        
        rating_inicial = RANGOS_CATEGORIAS.get(categoria_inicial)
        if not rating_inicial:
            usuarios_sin_categoria.append(f"{nombre} {apellido} (categoría: {categoria_inicial})")
            continue
        
        # Obtener suma de deltas
        query_deltas = text("""
            SELECT COALESCE(SUM(delta), 0) as suma
            FROM historial_rating
            WHERE id_usuario = :user_id
        """)
        
        result = session.execute(query_deltas, {"user_id": user_id}).fetchone()
        suma_deltas = int(result[0]) if result else 0
        
        rating_esperado = rating_inicial + suma_deltas
        diferencia = rating_actual - rating_esperado
        
        if diferencia != 0:
            usuarios_corregidos.append({
                'user_id': user_id,
                'nombre': f"{nombre} {apellido}",
                'rating_anterior': rating_actual,
                'rating_nuevo': rating_esperado,
                'diferencia': diferencia,
                'categoria': categoria_inicial
            })
            print(f"⚠️  {nombre} {apellido}: {rating_actual} → {rating_esperado} (diferencia: {diferencia:+d})")
        else:
            usuarios_correctos.append(f"{nombre} {apellido}")
    
    print(f"\n{'='*100}")
    print(f"\n📊 RESUMEN:")
    print(f"   Total usuarios verificados: {len(usuarios)}")
    print(f"   ⚠️  Usuarios con discrepancias: {len(usuarios_corregidos)}")
    print(f"   ✓  Usuarios correctos: {len(usuarios_correctos)}")
    print(f"   ⚠️  Usuarios sin categoría: {len(usuarios_sin_categoria)}")
    
    if usuarios_corregidos:
        print(f"\n{'='*100}")
        print(f"USUARIOS CON DISCREPANCIAS ({len(usuarios_corregidos)}):")
        print(f"{'='*100}")
        print(f"{'Nombre':<30} {'Categoría':<15} {'Actual':>6} {'Esperado':>8} {'Dif':>5}")
        print(f"{'-'*100}")
        for u in usuarios_corregidos:
            print(f"{u['nombre']:<30} {u['categoria']:<15} {u['rating_anterior']:>6} {u['rating_nuevo']:>8} {u['diferencia']:>+5}")
        
        print(f"\n{'='*100}")
        respuesta = input(f"¿Corregir los {len(usuarios_corregidos)} usuarios en PRODUCCIÓN? (s/n): ")
        if respuesta.lower() == 's':
            for u in usuarios_corregidos:
                query_update = text("""
                    UPDATE usuarios
                    SET rating = :rating
                    WHERE id_usuario = :user_id
                """)
                session.execute(query_update, {"rating": u['rating_nuevo'], "user_id": u['user_id']})
                print(f"✅ {u['nombre']}: {u['rating_anterior']} → {u['rating_nuevo']}")
            
            session.commit()
            print(f"\n✅ {len(usuarios_corregidos)} usuarios corregidos en PRODUCCIÓN")
        else:
            print("\n❌ Corrección cancelada")
    else:
        print(f"\n✅ Todos los usuarios tienen ratings correctos")
    
    if usuarios_sin_categoria:
        print(f"\n{'='*100}")
        print(f"⚠️  USUARIOS SIN CATEGORÍA ({len(usuarios_sin_categoria)}):")
        print(f"{'='*100}")
        for u in usuarios_sin_categoria:
            print(f"  {u}")

if __name__ == "__main__":
    try:
        verificar_y_corregir_todos()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
