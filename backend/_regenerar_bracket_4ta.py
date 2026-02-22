"""Eliminar playoffs viejos de 4ta T38 y regenerar con formato APA sin BYEs."""
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
CATEGORIA_4TA = 87
USER_ID = 2

# 1. Ver playoffs actuales
print("=== PLAYOFFS ACTUALES 4ta ===")
actuales = db.query(Partido).filter(
    Partido.id_torneo == TORNEO_ID,
    Partido.categoria_id == CATEGORIA_4TA,
    Partido.fase.in_(['8vos', '4tos', 'semis', 'final'])
).all()
for p in actuales:
    print(f"  P{p.id_partido} | {p.fase} #{p.numero_partido} | {p.estado} | p1={p.pareja1_id} p2={p.pareja2_id}")

print(f"\nTotal: {len(actuales)} partidos de playoff")

# 2. Verificar que ninguno tenga resultado
con_resultado = [p for p in actuales if p.estado == 'confirmado']
if con_resultado:
    print(f"\n⚠️ HAY {len(con_resultado)} PARTIDOS CON RESULTADO, NO SE PUEDE REGENERAR")
    db.close()
    exit(1)

# 3. Eliminar playoffs actuales
print("\n🗑️ Eliminando playoffs actuales...")
count = TorneoPlayoffService.eliminar_playoffs(db, TORNEO_ID, USER_ID, CATEGORIA_4TA)
print(f"  Eliminados: {count}")

# 4. Regenerar con formato APA
print("\n🔄 Regenerando con formato APA (sin BYEs)...")
partidos = TorneoPlayoffService.generar_playoffs(
    db, TORNEO_ID, USER_ID,
    clasificados_por_zona=2,
    categoria_id=CATEGORIA_4TA
)
print(f"  Creados: {len(partidos)} partidos")

# 5. Verificar resultado
print("\n=== NUEVO BRACKET 4ta ===")
nuevos = db.query(Partido).filter(
    Partido.id_torneo == TORNEO_ID,
    Partido.categoria_id == CATEGORIA_4TA,
    Partido.fase.in_(['8vos', '4tos', 'semis', 'final'])
).order_by(
    Partido.fase, Partido.numero_partido
).all()

for p in nuevos:
    p1_name = "---"
    p2_name = "---"
    if p.pareja1_id:
        r = db.execute(text("""
            SELECT pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
            FROM torneos_parejas tp
            JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
            JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
            WHERE tp.id = :pid
        """), {"pid": p.pareja1_id}).fetchone()
        if r: p1_name = r[0][:35]
    if p.pareja2_id:
        r = db.execute(text("""
            SELECT pf1.nombre || ' ' || pf1.apellido || ' / ' || pf2.nombre || ' ' || pf2.apellido
            FROM torneos_parejas tp
            JOIN perfil_usuarios pf1 ON tp.jugador1_id = pf1.id_usuario
            JOIN perfil_usuarios pf2 ON tp.jugador2_id = pf2.id_usuario
            WHERE tp.id = :pid
        """), {"pid": p.pareja2_id}).fetchone()
        if r: p2_name = r[0][:35]
    
    print(f"  P{p.id_partido} | {p.fase} #{p.numero_partido} | {p.estado}")
    print(f"    p1({p.pareja1_id}): {p1_name}")
    print(f"    p2({p.pareja2_id}): {p2_name}")

db.close()
