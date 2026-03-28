"""
Test directo del endpoint de ranking
"""
import os
from dotenv import load_dotenv
load_dotenv('.env.production')

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("TEST DIRECTO - QUERY SQL DEL RANKING")
print("=" * 80)
print()

with engine.connect() as conn:
    # Mismo SQL que usa el backend
    sql = """
        SELECT 
            cpj.usuario_id,
            u.nombre_usuario,
            p.nombre,
            p.apellido,
            COALESCE(tc.nombre, cpj.categoria_nombre) as categoria,
            SUM(cpj.puntos) as total_puntos,
            COUNT(DISTINCT COALESCE(cpj.torneo_externo, CAST(cpj.torneo_id AS TEXT))) as torneos_jugados
        FROM circuito_puntos_jugador cpj
        JOIN usuarios u ON cpj.usuario_id = u.id_usuario
        LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
        LEFT JOIN torneo_categorias tc ON cpj.categoria_id = tc.id
        WHERE cpj.circuito_id = 1
          AND (tc.nombre = '7ma' OR cpj.categoria_nombre = '7ma')
        GROUP BY cpj.usuario_id, u.nombre_usuario, p.nombre, p.apellido, COALESCE(tc.nombre, cpj.categoria_nombre)
        HAVING SUM(cpj.puntos) > 0
        ORDER BY total_puntos DESC
        LIMIT 10
    """
    
    rows = conn.execute(text(sql)).fetchall()
    
    print("TOP 10 - CATEGORÍA 7MA:")
    print("-" * 80)
    for i, r in enumerate(rows, 1):
        nombre = f"{r[2] or ''} {r[3] or ''}".strip() or r[1]
        print(f"{i:2d}. {nombre:40s} | {r[5]:5.0f} pts ({r[6]} torneos) | Cat: {r[4]}")
    
    print()
    print("=" * 80)
    print("MONTIVERO ESPECÍFICO:")
    print("=" * 80)
    
    # Ver todos los registros de Montivero
    sql2 = """
        SELECT 
            cpj.torneo_id,
            cpj.torneo_externo,
            COALESCE(tc.nombre, cpj.categoria_nombre) as categoria,
            cpj.fase_alcanzada,
            cpj.puntos
        FROM circuito_puntos_jugador cpj
        LEFT JOIN torneo_categorias tc ON cpj.categoria_id = tc.id
        WHERE cpj.usuario_id = 43 AND cpj.circuito_id = 1
        ORDER BY cpj.puntos DESC
    """
    
    registros = conn.execute(text(sql2)).fetchall()
    print(f"Total registros: {len(registros)}")
    print()
    for r in registros:
        torneo = r[1] if r[1] else f"T{r[0]}"
        print(f"  {r[2]:15s} | {torneo:40s} | {r[4]:4d} pts ({r[3]})")
    
    # Suma por categoría
    print()
    print("SUMA POR CATEGORÍA:")
    sql3 = """
        SELECT 
            COALESCE(tc.nombre, cpj.categoria_nombre) as categoria,
            SUM(cpj.puntos) as total
        FROM circuito_puntos_jugador cpj
        LEFT JOIN torneo_categorias tc ON cpj.categoria_id = tc.id
        WHERE cpj.usuario_id = 43 AND cpj.circuito_id = 1
        GROUP BY COALESCE(tc.nombre, cpj.categoria_nombre)
    """
    
    sumas = conn.execute(text(sql3)).fetchall()
    for s in sumas:
        print(f"  {s[0]:15s}: {s[1]:4d} pts")
