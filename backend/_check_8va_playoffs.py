"""Verificar playoffs 8va (cat 89) T38"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Zonas
result = db.execute(text("""
    SELECT id, nombre FROM torneo_zonas
    WHERE torneo_id = 38 AND categoria_id = 89
    ORDER BY numero_orden
"""))
zonas = result.fetchall()
print("=== ZONAS 8VA ===")
for z in zonas:
    print(f"  {z[1]} (id={z[0]})")

# Parejas por zona (via partidos de zona)
pareja_zona = {}
for z in zonas:
    zid, zname = z
    result = db.execute(text("""
        SELECT DISTINCT x.pid FROM (
            SELECT pareja1_id as pid FROM partidos WHERE zona_id = :zid AND fase = 'zona' AND pareja1_id IS NOT NULL
            UNION
            SELECT pareja2_id as pid FROM partidos WHERE zona_id = :zid AND fase = 'zona' AND pareja2_id IS NOT NULL
        ) x
    """), {"zid": zid})
    for r in result.fetchall():
        pareja_zona[r[0]] = zname

# Nombres
pareja_nombre = {}
all_pids = list(pareja_zona.keys())
if all_pids:
    plist = ','.join(str(p) for p in all_pids)
    result = db.execute(text(f"""
        SELECT tp.id,
               COALESCE(pu1.nombre,'') || ' ' || COALESCE(pu1.apellido,'') || '/' ||
               COALESCE(pu2.nombre,'') || ' ' || COALESCE(pu2.apellido,'')
        FROM torneos_parejas tp
        LEFT JOIN usuarios u1 ON tp.jugador1_id = u1.id_usuario
        LEFT JOIN perfil_usuarios pu1 ON u1.id_usuario = pu1.id_usuario
        LEFT JOIN usuarios u2 ON tp.jugador2_id = u2.id_usuario
        LEFT JOIN perfil_usuarios pu2 ON u2.id_usuario = pu2.id_usuario
        WHERE tp.id IN ({plist})
    """))
    for r in result.fetchall():
        pareja_nombre[r[0]] = r[1]

# Mostrar por zona
print("\n=== PAREJAS POR ZONA ===")
for z in zonas:
    zname = z[1]
    ps = [(pid, pareja_nombre.get(pid,'?')) for pid, zn in pareja_zona.items() if zn == zname]
    print(f"  {zname}: {ps}")

# Playoffs
print("\n=== PLAYOFFS 8VA ===")
result = db.execute(text("""
    SELECT id_partido, fase, numero_partido, pareja1_id, pareja2_id, 
           ganador_pareja_id, estado
    FROM partidos 
    WHERE id_torneo = 38 AND categoria_id = 89 
      AND fase IN ('8vos', '4tos', 'semis', 'final')
    ORDER BY 
        CASE fase WHEN '8vos' THEN 1 WHEN '4tos' THEN 2 WHEN 'semis' THEN 3 WHEN 'final' THEN 4 END,
        numero_partido
"""))
for p in result.fetchall():
    pid, fase, num, p1, p2, gan, est = p
    z1 = pareja_zona.get(p1, '?') if p1 else '-'
    z2 = pareja_zona.get(p2, '?') if p2 else '-'
    n1 = pareja_nombre.get(p1, '') if p1 else 'TBD'
    n2 = pareja_nombre.get(p2, '') if p2 else 'TBD'
    print(f"  P{pid}: {fase} #{num} [{est}] - ({z1}) {n1}  vs  ({z2}) {n2}")

print("\n=== FORMATO APA ESPERADO 5 ZONAS ===")
print("  8vos #1: BYE 1°A")
print("  8vos #2: 2°B vs 2°C")
print("  8vos #3: BYE 1°E")
print("  8vos #4: BYE 1°D")
print("  8vos #5: BYE 1°C")
print("  8vos #6: BYE 2°E")
print("  8vos #7: 2°A vs 2°D")
print("  8vos #8: BYE 1°B")

db.close()
