"""
Script para corregir ratings usando los RANGOS ESTÁNDAR de categorías
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

print(f"🔗 Conectando a producción...")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Rangos estándar de categorías
RANGOS_CATEGORIAS = {
    'Principiante': 249,
    '8va': 749,
    '7ma': 1099,
    '6ta': 1299,
    '5ta': 1499,
    '4ta': 1699,
    '3ra': 1899
}

def verificar_y_corregir_todos():
    """Verifica y corrige usando el rating_antes del PRIMER partido"""
    # Obtener todos los usuarios con historial de rating
    query = text("""
        SELECT DISTINCT u.id_usuario, p.nombre, p.apellido, u.rating
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        WHERE EXISTS (
            SELECT 1 FROM historial_rating h WHERE h.id_usuario = u.id_usuario
        )
        AND p.nombre NOT LIKE '%temp%'
        AND p.apellido NOT LIKE '%temp%'
        ORDER BY p.apellido, p.nombre
    """)
    
    usuarios = session.execute(query).fetchall()
    
    print(f"\n🔍 Verificando {len(usuarios)} usuarios (excluyendo temps)...\n")
    print(f"{'='*110}")
    
    usuarios_corregidos = []
    usuarios_correctos = []
    usuarios_sin_historial = []
    
    for user_id, nombre, apellido, rating_actual in usuarios:
        # Obtener el rating_antes del PRIMER partido (rating inicial real)
        query_primer_rating = text("""
            SELECT h.rating_antes
            FROM historial_rating h
            JOIN partidos pt ON h.id_partido = pt.id_partido
            WHERE h.id_usuario = :user_id
            ORDER BY pt.fecha ASC, h.id_historial ASC
            LIMIT 1
        """)
        
        primer_rating_row = session.execute(query_primer_rating, {"user_id": user_id}).fetchone()
        
        if not primer_rating_row:
            usuarios_sin_historial.append(f"{nombre} {apellido}")
            continue
        
        rating_inicial = primer_rating_row[0]
        
        # Obtener suma TOTAL de deltas (usando DISTINCT para evitar duplicados)
        query_suma_deltas = text("""
            SELECT COALESCE(SUM(delta), 0) as suma
            FROM (
                SELECT DISTINCT ON (id_usuario, id_partido) delta
                FROM historial_rating
                WHERE id_usuario = :user_id
                ORDER BY id_usuario, id_partido, id_historial
            ) t
        """)
        
        result = session.execute(query_suma_deltas, {"user_id": user_id}).fetchone()
        suma_deltas = int(result[0]) if result else 0
        
        rating_esperado = rating_inicial + suma_deltas
        diferencia = rating_actual - rating_esperado
        
        if diferencia != 0:
            usuarios_corregidos.append({
                'user_id': user_id,
                'nombre': f"{nombre} {apellido}",
                'rating_inicial': rating_inicial,
                'suma_deltas': suma_deltas,
                'rating_esperado': rating_esperado,
                'rating_actual': rating_actual,
                'diferencia': diferencia
            })
        else:
            usuarios_correctos.append(f"{nombre} {apellido}")
    
    print(f"\n{'='*110}")
    print(f"\n📊 RESUMEN:")
    print(f"   Total usuarios verificados: {len(usuarios)}")
    print(f"   ⚠️  Usuarios con discrepancias: {len(usuarios_corregidos)}")
    print(f"   ✓  Usuarios correctos: {len(usuarios_correctos)}")
    print(f"   ⚠️  Usuarios sin historial: {len(usuarios_sin_historial)}")
    print(f"\n{'='*110}")
    print(f"\n📊 RESUMEN:")
    print(f"   Total usuarios verificados: {len(usuarios)}")
    print(f"   ⚠️  Usuarios con discrepancias: {len(usuarios_corregidos)}")
    print(f"   ✓  Usuarios correctos: {len(usuarios_correctos)}")
    print(f"   ⚠️  Usuarios sin categoría: {len(usuarios_sin_categoria)}")
    
    if usuarios_corregidos:
        print(f"\n{'='*110}")
        print(f"USUARIOS CON DISCREPANCIAS ({len(usuarios_corregidos)}):")
        print(f"{'='*110}")
        print(f"{'Nombre':<30} {'Inicial':>8} {'Deltas':>7} {'Esperado':>9} {'Actual':>8} {'Dif':>6}")
        print(f"{'-'*110}")
        for u in usuarios_corregidos:
            print(f"{u['nombre']:<30} {u['rating_inicial']:>8} {u['suma_deltas']:>+7} {u['rating_esperado']:>9} {u['rating_actual']:>8} {u['diferencia']:>+6}")
        
        print(f"\n{'='*110}")
        print(f"NOTA: Estos usuarios tienen ratings que NO coinciden con: rating_inicial + suma_deltas")
        print(f"      El rating_inicial es el rating_antes del primer partido en su historial.")
        print(f"{'='*110}")
        respuesta = input(f"\n¿Corregir los {len(usuarios_corregidos)} usuarios en PRODUCCIÓN? (s/n): ")
        if respuesta.lower() == 's':
            for u in usuarios_corregidos:
                query_update = text("""
                    UPDATE usuarios
                    SET rating = :rating
                    WHERE id_usuario = :user_id
                """)
                session.execute(query_update, {"rating": u['rating_esperado'], "user_id": u['user_id']})
                print(f"✅ {u['nombre']}: {u['rating_actual']} → {u['rating_esperado']}")
            
            session.commit()
            print(f"\n✅ {len(usuarios_corregidos)} usuarios corregidos en PRODUCCIÓN")
        else:
            print("\n❌ Corrección cancelada")
    else:
        print(f"\n✅ Todos los usuarios tienen ratings correctos")

if __name__ == "__main__":
    try:
        verificar_y_corregir_todos()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
