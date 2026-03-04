"""
Analizar casos específicos para entender discrepancias
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv('.env.production')

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

RANGOS_CATEGORIAS = {
    'Principiante': 249,
    '8va': 749,
    '7ma': 1099,
    '6ta': 1299,
    '5ta': 1499,
    '4ta': 1699,
    '3ra': 1899
}

def analizar_usuario(nombre_completo):
    """Analiza el historial completo de un usuario"""
    partes = nombre_completo.split()
    nombre = partes[0]
    apellido = ' '.join(partes[1:])
    
    query = text("""
        SELECT u.id_usuario, p.nombre, p.apellido, u.rating, c.nombre as categoria
        FROM usuarios u
        JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        LEFT JOIN categorias c ON u.id_categoria = c.id_categoria
        WHERE p.nombre ILIKE :nombre AND p.apellido ILIKE :apellido
    """)
    
    usuario = session.execute(query, {"nombre": nombre, "apellido": apellido}).fetchone()
    
    if not usuario:
        print(f"❌ Usuario no encontrado: {nombre_completo}")
        return
    
    user_id, nombre, apellido, rating_actual, categoria = usuario
    
    print(f"\n{'='*100}")
    print(f"👤 Usuario: {nombre} {apellido} (ID: {user_id})")
    print(f"📊 Rating actual en BD: {rating_actual}")
    print(f"🎯 Categoría: {categoria}")
    print(f"🎯 Rating inicial estándar: {RANGOS_CATEGORIAS.get(categoria, 'N/A')}")
    
    # Obtener historial completo
    query_historial = text("""
        SELECT h.id_partido, h.delta, h.rating_antes, h.rating_despues, p.fecha
        FROM historial_rating h
        JOIN partidos p ON h.id_partido = p.id_partido
        WHERE h.id_usuario = :user_id
        ORDER BY p.fecha ASC
    """)
    
    historial = session.execute(query_historial, {"user_id": user_id}).fetchall()
    
    print(f"\n📈 Historial de partidos ({len(historial)} partidos):")
    print(f"{'Partido':<10} {'Delta':>7} {'Antes':>7} {'Después':>9} {'Fecha':<30}")
    print(f"{'-'*100}")
    
    for id_partido, delta, antes, despues, fecha in historial:
        print(f"{id_partido:<10} {delta:>+7} {antes:>7} {despues:>9} {str(fecha):<30}")
    
    if historial:
        primer_rating = historial[0][2]  # rating_antes del primer partido
        suma_deltas = sum(h[1] for h in historial)
        rating_esperado_desde_primer = primer_rating + suma_deltas
        rating_esperado_desde_categoria = RANGOS_CATEGORIAS.get(categoria, 0) + suma_deltas
        
        print(f"\n{'='*100}")
        print(f"📊 ANÁLISIS:")
        print(f"   Primer rating (historial):     {primer_rating}")
        print(f"   Rating inicial (categoría):    {RANGOS_CATEGORIAS.get(categoria, 'N/A')}")
        print(f"   Suma de deltas:                {suma_deltas:+d}")
        print(f"   Rating esperado (desde primer): {rating_esperado_desde_primer}")
        print(f"   Rating esperado (desde cat):    {rating_esperado_desde_categoria}")
        print(f"   Rating actual:                  {rating_actual}")
        print(f"   Diferencia (vs primer):         {rating_actual - rating_esperado_desde_primer:+d}")
        print(f"   Diferencia (vs categoría):      {rating_actual - rating_esperado_desde_categoria:+d}")
        print(f"{'='*100}\n")

# Analizar casos específicos
casos = [
    "Dario Barrionuevo",
    "Matias Giordano",
    "Leandro Ruarte",
    "Damian Tapia",
    "Juan Loto",
    "Victoria Cavalleri"
]

for caso in casos:
    analizar_usuario(caso)

session.close()
