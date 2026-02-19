"""
Cargar puntos del torneo 37 al sistema de circuitos.
Primero diagnostica la estructura, luego carga los puntos.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# 1. Agregar fases 8vos y 16avos a la config de puntos
print("=== Actualizando configuración de puntos ===")
db.execute(text("""
INSERT INTO circuito_puntos_fase (circuito_id, fase, puntos)
SELECT c.id, v.fase, v.puntos
FROM circuitos c
CROSS JOIN (VALUES 
    ('campeon', 1000),
    ('subcampeon', 800),
    ('semis', 600),
    ('cuartos', 400),
    ('8vos', 200),
    ('16avos', 150),
    ('zona', 100)
) AS v(fase, puntos)
WHERE c.codigo = 'zf'
ON CONFLICT (circuito_id, fase) DO UPDATE SET puntos = EXCLUDED.puntos
"""))
db.commit()

result = db.execute(text("SELECT fase, puntos FROM circuito_puntos_fase ORDER BY puntos DESC")).fetchall()
print("Puntos configurados:")
for r in result:
    print(f"  {r[0]}: {r[1]} pts")

# 2. Ver estructura del torneo 37
print("\n=== Categorías del torneo 37 ===")
cats = db.execute(text("SELECT id, nombre FROM torneo_categorias WHERE torneo_id = 37")).fetchall()
for c in cats:
    print(f"  ID {c[0]}: {c[1]}")

# 3. Ver partidos de playoffs
print("\n=== Partidos de playoffs del torneo 37 ===")
partidos = db.execute(text("""
    SELECT p.id_partido, p.fase, p.categoria_id, tc.nombre as cat_nombre,
           p.pareja1_id, p.pareja2_id, p.estado
    FROM partidos p
    LEFT JOIN torneo_categorias tc ON p.categoria_id = tc.id
    WHERE p.id_torneo = 37 AND p.fase IS NOT NULL AND p.fase != 'zona'
    ORDER BY tc.nombre, 
        CASE p.fase 
            WHEN 'final' THEN 1 
            WHEN 'semis' THEN 2 
            WHEN '4tos' THEN 3 
            WHEN '8vos' THEN 4 
            WHEN '16avos' THEN 5 
        END,
        p.id_partido
""")).fetchall()

for p in partidos:
    print(f"  Partido {p[0]}: fase={p[1]}, cat={p[2]}({p[3]}), p1={p[4]}, p2={p[5]}, estado={p[6]}")

# 4. Ver parejas con jugadores
print("\n=== Parejas del torneo 37 ===")
parejas = db.execute(text("""
    SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.categoria_id, tc.nombre,
           p1.nombre || ' ' || p1.apellido as j1,
           p2.nombre || ' ' || p2.apellido as j2
    FROM torneos_parejas tp
    LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
    LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
    LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
    WHERE tp.torneo_id = 37 AND tp.estado != 'baja'
    ORDER BY tc.nombre, tp.id
""")).fetchall()

for p in parejas:
    print(f"  Pareja {p[0]}: {p[5]} / {p[6]} (cat: {p[4]})")

# 5. Ver resultados de partidos de playoffs para determinar ganadores
print("\n=== Resultados de playoffs ===")
resultados = db.execute(text("""
    SELECT p.id_partido, p.fase, p.categoria_id, tc.nombre,
           p.pareja1_id, p.pareja2_id,
           rs.sets_eq1, rs.sets_eq2
    FROM partidos p
    LEFT JOIN torneo_categorias tc ON p.categoria_id = tc.id
    LEFT JOIN resultado_partidos rs ON p.id_partido = rs.id_partido
    WHERE p.id_torneo = 37 AND p.fase IS NOT NULL AND p.fase != 'zona'
    ORDER BY tc.nombre, p.fase, p.id_partido
""")).fetchall()

for r in resultados:
    ganador = r[4] if (r[6] or 0) > (r[7] or 0) else r[5] if (r[7] or 0) > (r[6] or 0) else None
    print(f"  Partido {r[0]}: fase={r[1]}, cat={r[3]}, p1={r[4]} vs p2={r[5]}, sets={r[6]}-{r[7]}, ganador_pareja={ganador}")

db.close()
