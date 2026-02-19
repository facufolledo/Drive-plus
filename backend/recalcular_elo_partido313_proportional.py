"""
Recalcular ELO del partido 313 con modo proportional.
El delta total del equipo no cambia, solo se redistribuye entre los jugadores.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()
ID_PARTIDO = 313

print("=== RECALCULAR REPARTO ELO PARTIDO 313 (proportional) ===\n")

# Obtener datos actuales
jugadores = db.execute(text("""
    SELECT pj.id_usuario, pj.equipo, pj.rating_antes, pj.rating_despues, pj.cambio_elo,
           COALESCE(pu.nombre || ' ' || pu.apellido, u.nombre_usuario) as nombre
    FROM partido_jugadores pj
    JOIN usuarios u ON pj.id_usuario = u.id_usuario
    LEFT JOIN perfil_usuarios pu ON pj.id_usuario = pu.id_usuario
    WHERE pj.id_partido = :pid
    ORDER BY pj.equipo, pj.id_usuario
"""), {"pid": ID_PARTIDO}).fetchall()

print("ANTES (inverse):")
for j in jugadores:
    signo = "+" if j[4] > 0 else ""
    print(f"  Equipo {j[1]}: {j[5]} (ID:{j[0]}, rating_antes={j[2]}) | delta: {signo}{j[4]}")

# Agrupar por equipo
equipo1 = [j for j in jugadores if j[1] == 1]
equipo2 = [j for j in jugadores if j[1] == 2]

def split_proportional(delta_total, r1, r2):
    """Reparto proportional: jugador de mayor rating absorbe más"""
    w1 = max(1.0, r1)
    w2 = max(1.0, r2)
    s = w1 + w2
    return delta_total * (w1 / s), delta_total * (w2 / s)

# Calcular delta total por equipo (suma de cambio_elo actuales)
delta_eq1 = sum(j[4] for j in equipo1)
delta_eq2 = sum(j[4] for j in equipo2)

print(f"\nDelta total equipo 1: {delta_eq1}")
print(f"Delta total equipo 2: {delta_eq2}")

# Redistribuir con proportional
d1_a, d1_b = split_proportional(delta_eq1, equipo1[0][2], equipo1[1][2])
d2_a, d2_b = split_proportional(delta_eq2, equipo2[0][2], equipo2[1][2])

nuevos_deltas = {
    equipo1[0][0]: int(round(d1_a)),
    equipo1[1][0]: int(round(d1_b)),
    equipo2[0][0]: int(round(d2_a)),
    equipo2[1][0]: int(round(d2_b)),
}

print(f"\nNuevos deltas (proportional):")
for j in jugadores:
    uid = j[0]
    nuevo_delta = nuevos_deltas[uid]
    signo = "+" if nuevo_delta > 0 else ""
    print(f"  {j[5]} (ID:{uid}, rating={j[2]}): {signo}{nuevo_delta}")

# Aplicar cambios
for j in jugadores:
    uid = j[0]
    rating_antes = j[2]
    delta_viejo = j[4]
    delta_nuevo = nuevos_deltas[uid]
    rating_despues_nuevo = rating_antes + delta_nuevo
    diferencia = delta_nuevo - delta_viejo
    
    # Actualizar partido_jugadores
    db.execute(text("""
        UPDATE partido_jugadores 
        SET cambio_elo = :delta, rating_despues = :rd
        WHERE id_partido = :pid AND id_usuario = :uid
    """), {"delta": delta_nuevo, "rd": rating_despues_nuevo, "pid": ID_PARTIDO, "uid": uid})
    
    # Actualizar historial_rating
    db.execute(text("""
        UPDATE historial_rating 
        SET delta = :delta, rating_despues = :rd
        WHERE id_partido = :pid AND id_usuario = :uid
    """), {"delta": delta_nuevo, "rd": rating_despues_nuevo, "pid": ID_PARTIDO, "uid": uid})
    
    # Actualizar rating actual del usuario
    db.execute(text("""
        UPDATE usuarios SET rating = rating + :diff WHERE id_usuario = :uid
    """), {"diff": diferencia, "uid": uid})

db.commit()

# Verificar
print("\nDESPUÉS (proportional):")
jugadores_fix = db.execute(text("""
    SELECT pj.id_usuario, pj.equipo, pj.rating_antes, pj.rating_despues, pj.cambio_elo,
           COALESCE(pu.nombre || ' ' || pu.apellido, u.nombre_usuario) as nombre,
           u.rating as rating_actual
    FROM partido_jugadores pj
    JOIN usuarios u ON pj.id_usuario = u.id_usuario
    LEFT JOIN perfil_usuarios pu ON pj.id_usuario = pu.id_usuario
    WHERE pj.id_partido = :pid
    ORDER BY pj.equipo, pj.id_usuario
"""), {"pid": ID_PARTIDO}).fetchall()

for j in jugadores_fix:
    signo = "+" if j[4] > 0 else ""
    print(f"  Equipo {j[1]}: {j[5]} (ID:{j[0]}) | {j[2]} {signo}{j[4]} -> {j[3]} | rating actual: {j[6]}")

db.close()
print("\n✅ Recalculado con modo proportional!")
