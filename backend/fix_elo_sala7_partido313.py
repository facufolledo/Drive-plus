"""
Fix ELO invertido en partido 313 (Sala 7)
Bug: equipo 2 ganó pero recibió deltas negativos, equipo 1 perdió pero recibió positivos.
Causa: resultado_padel era None, lo que hacía equipo1_es_equipoA=False e invertía los sets.

Jugadores afectados:
- Equipo 1 (PERDEDORES): Folledo (ID:2) +9 -> debe ser -9, Lopez (ID:77) +6 -> debe ser -6
- Equipo 2 (GANADORES): Lucero (ID:19) -8 -> debe ser +8, Boetto (ID:229) -7 -> debe ser +7
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()
ID_PARTIDO = 313

print("=== FIX ELO INVERTIDO - PARTIDO 313 (SALA 7) ===\n")

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

print("ANTES del fix:")
for j in jugadores:
    signo = "+" if j[4] > 0 else ""
    print(f"  Equipo {j[1]}: {j[5]} (ID:{j[0]}) | {j[2]} {signo}{j[4]} -> {j[3]}")

# Para cada jugador, invertir el delta
for j in jugadores:
    uid = j[0]
    rating_antes = j[2]
    delta_viejo = j[4]
    delta_nuevo = -delta_viejo  # Invertir
    rating_despues_nuevo = rating_antes + delta_nuevo
    
    # 1. Actualizar partido_jugadores
    db.execute(text("""
        UPDATE partido_jugadores 
        SET cambio_elo = :delta, rating_despues = :rating_despues
        WHERE id_partido = :pid AND id_usuario = :uid
    """), {"delta": delta_nuevo, "rating_despues": rating_despues_nuevo, "pid": ID_PARTIDO, "uid": uid})
    
    # 2. Actualizar historial_rating
    db.execute(text("""
        UPDATE historial_rating 
        SET delta = :delta, rating_despues = :rating_despues
        WHERE id_partido = :pid AND id_usuario = :uid
    """), {"delta": delta_nuevo, "rating_despues": rating_despues_nuevo, "pid": ID_PARTIDO, "uid": uid})
    
    # 3. Actualizar rating actual del usuario
    # rating_actual = rating_antes + delta_nuevo (en vez del delta_viejo que ya se aplicó)
    # Diferencia = delta_nuevo - delta_viejo = -2 * delta_viejo
    diferencia = delta_nuevo - delta_viejo
    db.execute(text("""
        UPDATE usuarios SET rating = rating + :diff WHERE id_usuario = :uid
    """), {"diff": diferencia, "uid": uid})

db.commit()

# Verificar resultado
print("\nDESPUÉS del fix:")
jugadores_fix = db.execute(text("""
    SELECT pj.id_usuario, pj.equipo, pj.rating_antes, pj.rating_despues, pj.cambio_elo,
           COALESCE(pu.nombre || ' ' || pu.apellido, u.nombre_usuario) as nombre
    FROM partido_jugadores pj
    JOIN usuarios u ON pj.id_usuario = u.id_usuario
    LEFT JOIN perfil_usuarios pu ON pj.id_usuario = pu.id_usuario
    WHERE pj.id_partido = :pid
    ORDER BY pj.equipo, pj.id_usuario
"""), {"pid": ID_PARTIDO}).fetchall()

for j in jugadores_fix:
    signo = "+" if j[4] > 0 else ""
    print(f"  Equipo {j[1]}: {j[5]} (ID:{j[0]}) | {j[2]} {signo}{j[4]} -> {j[3]}")

print("\nRatings actuales en tabla usuarios:")
for j in jugadores_fix:
    r = db.execute(text("SELECT rating FROM usuarios WHERE id_usuario = :uid"), {"uid": j[0]}).fetchone()
    print(f"  {j[5]} (ID:{j[0]}): rating = {r[0]}")

print("\nHistorial rating:")
for j in jugadores_fix:
    h = db.execute(text("""
        SELECT rating_antes, delta, rating_despues FROM historial_rating 
        WHERE id_partido = :pid AND id_usuario = :uid
    """), {"pid": ID_PARTIDO, "uid": j[0]}).fetchone()
    if h:
        signo = "+" if h[1] > 0 else ""
        print(f"  {j[5]} (ID:{j[0]}): {h[0]} {signo}{h[1]} -> {h[2]}")

db.close()
print("\n✅ Fix completado!")
