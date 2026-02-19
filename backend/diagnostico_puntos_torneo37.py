"""
Diagnóstico completo para cargar puntos del torneo 37.
Usa ganador_pareja_id y resultados_partidos para determinar ganadores.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== PARTIDOS PLAYOFFS TORNEO 37 CON GANADOR ===")
partidos = db.execute(text("""
    SELECT p.id_partido, p.fase, p.categoria_id, tc.nombre as cat,
           p.pareja1_id, p.pareja2_id, p.estado, p.ganador_pareja_id,
           rp.sets_eq1, rp.sets_eq2
    FROM partidos p
    LEFT JOIN torneo_categorias tc ON p.categoria_id = tc.id
    LEFT JOIN resultados_partidos rp ON p.id_partido = rp.id_partido
    WHERE p.id_torneo = 37 AND p.fase IS NOT NULL AND p.fase != 'zona'
    ORDER BY tc.nombre, 
        CASE p.fase 
            WHEN 'final' THEN 1 
            WHEN 'semis' THEN 2 
            WHEN '4tos' THEN 3 
        END,
        p.id_partido
""")).fetchall()

for p in partidos:
    print(f"  [{p[3]}] {p[1]:8s} | P{p[0]:4d} | {p[4]} vs {p[5]} | estado={p[6]} | ganador={p[7]} | sets={p[8]}-{p[9]}")

print("\n=== PAREJAS TORNEO 37 CON JUGADORES ===")
parejas = db.execute(text("""
    SELECT tp.id, tp.jugador1_id, tp.jugador2_id, tp.categoria_id, tc.nombre,
           COALESCE(p1.nombre || ' ' || p1.apellido, 'N/A') as j1,
           COALESCE(p2.nombre || ' ' || p2.apellido, 'N/A') as j2
    FROM torneos_parejas tp
    LEFT JOIN torneo_categorias tc ON tp.categoria_id = tc.id
    LEFT JOIN perfil_usuarios p1 ON tp.jugador1_id = p1.id_usuario
    LEFT JOIN perfil_usuarios p2 ON tp.jugador2_id = p2.id_usuario
    WHERE tp.torneo_id = 37 AND tp.estado != 'baja'
    ORDER BY tc.nombre, tp.id
""")).fetchall()

for p in parejas:
    print(f"  Pareja {p[0]:4d} [{p[4]}]: {p[5]} (ID:{p[1]}) / {p[6]} (ID:{p[2]})")

print("\n=== CIRCUITO ZF CONFIG ===")
config = db.execute(text("SELECT fase, puntos FROM circuito_puntos_fase cpf JOIN circuitos c ON cpf.circuito_id = c.id WHERE c.codigo = 'zf' ORDER BY puntos DESC")).fetchall()
for c in config:
    print(f"  {c[0]}: {c[1]} pts")

print("\n=== CIRCUITO ZF ID ===")
circ = db.execute(text("SELECT id, codigo, nombre FROM circuitos WHERE codigo = 'zf'")).fetchone()
if circ:
    print(f"  ID: {circ[0]}, Codigo: {circ[1]}, Nombre: {circ[2]}")

db.close()
