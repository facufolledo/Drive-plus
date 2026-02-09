"""
Script para probar el fix del ranking
Simula la query que hace el endpoint
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno de PRODUCCIÓN
load_dotenv('.env.production')

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ No se encontró DATABASE_URL")
    exit(1)

# Importar modelos
import sys
sys.path.append('src')

from models.driveplus_models import Usuario, PerfilUsuario, Categoria, HistorialRating, Partido

# Crear engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("🔍 Probando fix del ranking")
print("=" * 70)

try:
    # Subquery para calcular partidos JUGADOS desde historial_rating
    partidos_jugados_subq = (
        db.query(
            HistorialRating.id_usuario,
            func.count(func.distinct(HistorialRating.id_partido)).label("partidos_jugados_real")
        )
        .join(Partido, HistorialRating.id_partido == Partido.id_partido)
        .filter(
            Partido.estado.in_(["finalizado", "confirmado"])
        )
        .group_by(HistorialRating.id_usuario)
        .subquery()
    )
    
    # Subquery para calcular partidos ganados desde historial_rating
    partidos_ganados_subq = (
        db.query(
            HistorialRating.id_usuario,
            func.count(HistorialRating.id_partido).label("partidos_ganados")
        )
        .join(Partido, HistorialRating.id_partido == Partido.id_partido)
        .filter(
            Partido.estado.in_(["finalizado", "confirmado"]),
            HistorialRating.delta > 0  # Delta positivo = victoria
        )
        .group_by(HistorialRating.id_usuario)
        .subquery()
    )
    
    # Subquery para calcular tendencia
    tendencia_subq = (
        db.query(
            HistorialRating.id_usuario,
            func.sum(HistorialRating.delta).label("suma_deltas")
        )
        .join(Partido, HistorialRating.id_partido == Partido.id_partido)
        .filter(Partido.estado.in_(["finalizado", "confirmado"]))
        .group_by(HistorialRating.id_usuario)
        .subquery()
    )
    
    # Query principal
    query = (
        db.query(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Usuario.rating,
            func.coalesce(partidos_jugados_subq.c.partidos_jugados_real, 0).label("partidos_jugados"),
            Usuario.sexo,
            PerfilUsuario.nombre,
            PerfilUsuario.apellido,
            Categoria.nombre.label("categoria_nombre"),
            func.coalesce(partidos_ganados_subq.c.partidos_ganados, 0).label("partidos_ganados"),
            func.coalesce(tendencia_subq.c.suma_deltas, 0).label("suma_deltas")
        )
        .join(PerfilUsuario, Usuario.id_usuario == PerfilUsuario.id_usuario, isouter=True)
        .join(Categoria, Usuario.id_categoria == Categoria.id_categoria, isouter=True)
        .join(partidos_jugados_subq, Usuario.id_usuario == partidos_jugados_subq.c.id_usuario, isouter=True)
        .join(partidos_ganados_subq, Usuario.id_usuario == partidos_ganados_subq.c.id_usuario, isouter=True)
        .join(tendencia_subq, Usuario.id_usuario == tendencia_subq.c.id_usuario, isouter=True)
        .order_by(Usuario.rating.desc())
        .limit(10)
    )
    
    usuarios = query.all()
    
    print(f"\n✅ Top 10 usuarios con el FIX aplicado:\n")
    
    for i, u in enumerate(usuarios, 1):
        suma_deltas = u.suma_deltas or 0
        
        # Calcular tendencia
        if suma_deltas > 10:
            tendencia = "up ↑"
        elif suma_deltas < -10:
            tendencia = "down ↓"
        elif suma_deltas != 0:
            tendencia = "stable →"
        else:
            tendencia = "neutral --"
        
        porcentaje = 0
        if u.partidos_jugados > 0:
            porcentaje = round((u.partidos_ganados / u.partidos_jugados) * 100)
        
        print(f"{i}. {u.nombre} {u.apellido} (@{u.nombre_usuario})")
        print(f"   Rating: {u.rating} | Categoría: {u.categoria_nombre}")
        print(f"   Partidos: {u.partidos_jugados} | Ganados: {u.partidos_ganados} | Win%: {porcentaje}%")
        print(f"   Tendencia: {tendencia} (Δ={suma_deltas})")
        print()
    
    # Verificar que hay usuarios con partidos > 0
    usuarios_con_partidos = [u for u in usuarios if u.partidos_jugados > 0]
    
    if usuarios_con_partidos:
        print(f"✅ FIX FUNCIONANDO: {len(usuarios_con_partidos)} usuarios tienen partidos > 0")
    else:
        print(f"⚠️  PROBLEMA: Ningún usuario tiene partidos > 0")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
