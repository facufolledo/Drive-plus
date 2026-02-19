"""Test del nuevo endpoint de ranking por puntos de fase"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Simular lo que hace el endpoint
print("=== RANKING 7ma ===")
rows = db.execute(text("""
    SELECT cpj.usuario_id, u.nombre_usuario, 
           COALESCE(p.nombre || ' ' || p.apellido, u.nombre_usuario) as nombre_completo,
           tc.nombre as categoria, cpj.fase_alcanzada, 
           SUM(cpj.puntos) as total_puntos,
           COUNT(DISTINCT cpj.torneo_id) as torneos
    FROM circuito_puntos_jugador cpj
    JOIN circuitos c ON cpj.circuito_id = c.id
    JOIN usuarios u ON cpj.usuario_id = u.id_usuario
    LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
    LEFT JOIN torneo_categorias tc ON cpj.categoria_id = tc.id
    WHERE c.codigo = 'zf' AND tc.nombre = '7ma'
    GROUP BY cpj.usuario_id, u.nombre_usuario, p.nombre, p.apellido, tc.nombre, cpj.fase_alcanzada
    ORDER BY total_puntos DESC
""")).fetchall()

for r in rows:
    print(f"  {r[2]:30s} | {r[4]:12s} | {r[5]:5d} pts | {r[6]} torneos")

print("\n=== RANKING Principiante ===")
rows = db.execute(text("""
    SELECT cpj.usuario_id, 
           COALESCE(p.nombre || ' ' || p.apellido, u.nombre_usuario) as nombre_completo,
           tc.nombre as categoria, cpj.fase_alcanzada, 
           SUM(cpj.puntos) as total_puntos
    FROM circuito_puntos_jugador cpj
    JOIN circuitos c ON cpj.circuito_id = c.id
    JOIN usuarios u ON cpj.usuario_id = u.id_usuario
    LEFT JOIN perfil_usuarios p ON u.id_usuario = p.id_usuario
    LEFT JOIN torneo_categorias tc ON cpj.categoria_id = tc.id
    WHERE c.codigo = 'zf' AND tc.nombre = 'Principiante'
    GROUP BY cpj.usuario_id, u.nombre_usuario, p.nombre, p.apellido, tc.nombre, cpj.fase_alcanzada
    ORDER BY total_puntos DESC
""")).fetchall()

for r in rows:
    print(f"  {r[1]:30s} | {r[3]:12s} | {r[4]:5d} pts")

print(f"\nTotal registros en circuito_puntos_jugador: {db.execute(text('SELECT COUNT(*) FROM circuito_puntos_jugador')).scalar()}")
db.close()
