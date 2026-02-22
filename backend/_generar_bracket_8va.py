"""Generar bracket 8va T38 con formato APA (5 zonas)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from src.database.config import SessionLocal
from src.services.torneo_playoff_service import TorneoPlayoffService
from src.models.driveplus_models import Partido
from sqlalchemy import text

db = SessionLocal()

TORNEO_ID = 38
CATEGORIA_8VA = 89
USER_ID = 2

# 1. Verificar que no haya playoffs existentes
actuales = db.query(Partido).filter(
    Partido.id_torneo == TORNEO_ID,
    Partido.categoria_id == CATEGORIA_8VA,
    Partido.fase.in_(['16avos', '8vos', '4tos', 'semis', 'final'])
).all()

if actuales:
    con_resultado = [p for p in actuales if p.estado == 'confirmado']
    if con_resultado:
        print(f"⚠️ HAY {len(con_resultado)} PARTIDOS CON RESULTADO, NO SE PUEDE REGENERAR")
        db.close()
        exit(1)
    print(f"🗑️ Eliminando {len(actuales)} playoffs existentes...")
    count = TorneoPlayoffService.eliminar_playoffs(db, TORNEO_ID, USER_ID, CATEGORIA_8VA)
    print(f"  Eliminados: {count}")
else:
    print("No hay playoffs previos, generando desde cero...")

# 2. Generar con formato APA
print("\n🔄 Generando bracket APA 8va (5 zonas)...")
partidos = TorneoPlayoffService.generar_playoffs(
    db, TORNEO_ID, USER_ID,
    clasificados_por_zona=2,
    categoria_id=CATEGORIA_8VA
)
print(f"  Creados: {len(partidos)} partidos")

# 3. Verificar resultado
print("\n=== BRACKET 8VA ===")
nuevos = db.query(Partido).filter(
    Partido.id_torneo == TORNEO_ID,
    Partido.categoria_id == CATEGORIA_8VA,
    Partido.fase.in_(['8vos', '4tos', 'semis', 'final'])
).order_by(
    Partido.fase, Partido.numero_partido
).all()

# Mapear parejas a zonas
pareja_zona = {}
zonas = db.execute(text("""
    SELECT id, nombre FROM torneo_zonas
    WHERE torneo_id = 38 AND categoria_id = 89 ORDER BY numero_orden
""")).fetchall()
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

for p in nuevos:
    p1_name = "TBD"
    p2_name = "TBD"
    z1 = pareja_zona.get(p.pareja1_id, '?') if p.pareja1_id else '-'
    z2 = pareja_zona.get(p.pareja2_id, '?') if p.pareja2_id else '-'
    if p.pareja1_id:
        r = db.execute(text("""
            SELECT COALESCE(pf1.nombre,'') || ' ' || COALESCE(pf1.apellido,'') || ' / ' || 
                   COALESCE(pf2.nombre,'') || ' ' || COALESCE(pf2.apellido,'')
            FROM torneos_parejas tp
            LEFT JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
            LEFT JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
            WHERE tp.id = :pid
        """), {"pid": p.pareja1_id}).fetchone()
        if r: p1_name = r[0][:40]
    if p.pareja2_id:
        r = db.execute(text("""
            SELECT COALESCE(pf1.nombre,'') || ' ' || COALESCE(pf1.apellido,'') || ' / ' || 
                   COALESCE(pf2.nombre,'') || ' ' || COALESCE(pf2.apellido,'')
            FROM torneos_parejas tp
            LEFT JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
            LEFT JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
            WHERE tp.id = :pid
        """), {"pid": p.pareja2_id}).fetchone()
        if r: p2_name = r[0][:40]
    
    print(f"  P{p.id_partido} | {p.fase} #{p.numero_partido} | {p.estado}")
    print(f"    p1({p.pareja1_id}) [{z1}]: {p1_name}")
    print(f"    p2({p.pareja2_id}) [{z2}]: {p2_name}")

print("\nFormato APA esperado para 5 zonas:")
print("  8vos #1: BYE 1°A       → 4tos#1 p1")
print("  8vos #2: 2°B vs 2°C    → 4tos#1 p2")
print("  8vos #3: BYE 1°E       → 4tos#2 p1")
print("  8vos #4: BYE 1°D       → 4tos#2 p2")
print("  8vos #5: BYE 1°C       → 4tos#3 p1")
print("  8vos #6: BYE 2°E       → 4tos#3 p2")  
print("  8vos #7: 2°A vs 2°D    → 4tos#4 p1")
print("  8vos #8: BYE 1°B       → 4tos#4 p2")

db.close()
