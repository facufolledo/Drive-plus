"""Ejecutar migración de puntos por fase para circuitos"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Insertar puntos por defecto para circuito zf
db.execute(text("""
INSERT INTO circuito_puntos_fase (circuito_id, fase, puntos)
SELECT c.id, v.fase, v.puntos
FROM circuitos c
CROSS JOIN (VALUES 
    ('campeon', 1000),
    ('subcampeon', 800),
    ('semis', 600),
    ('cuartos', 400),
    ('zona', 100)
) AS v(fase, puntos)
WHERE c.codigo = 'zf'
ON CONFLICT (circuito_id, fase) DO UPDATE SET puntos = EXCLUDED.puntos
"""))
db.commit()

result = db.execute(text("SELECT fase, puntos FROM circuito_puntos_fase ORDER BY puntos DESC")).fetchall()
print("Puntos configurados para circuito zf:")
for r in result:
    print(f"  {r[0]}: {r[1]} pts")

db.close()
print("\nMigración completada!")
