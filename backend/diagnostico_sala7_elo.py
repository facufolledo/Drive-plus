"""Diagnóstico ELO invertido en sala 7"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from src.database.config import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== PARTIDO DE SALA 7 ===")
partido = db.execute(text("""
    SELECT p.id_partido, p.id_sala, p.estado, p.ganador_equipo, p.elo_aplicado,
           p.resultado_padel, p.estado_confirmacion
    FROM partidos p WHERE p.id_sala = 7
""")).fetchone()

if partido:
    print(f"  Partido ID: {partido[0]}, estado: {partido[2]}, ganador_equipo: {partido[3]}, elo_aplicado: {partido[4]}")
    print(f"  resultado_padel: {partido[5]}")
    print(f"  estado_confirmacion: {partido[6]}")
    
    pid = partido[0]
    
    print("\n=== JUGADORES DEL PARTIDO ===")
    jugadores = db.execute(text("""
        SELECT pj.id_usuario, pj.equipo, pj.rating_antes, pj.rating_despues, pj.cambio_elo,
               COALESCE(pu.nombre || ' ' || pu.apellido, u.nombre_usuario) as nombre
        FROM partido_jugadores pj
        JOIN usuarios u ON pj.id_usuario = u.id_usuario
        LEFT JOIN perfil_usuarios pu ON pj.id_usuario = pu.id_usuario
        WHERE pj.id_partido = :pid
        ORDER BY pj.equipo, pj.id_usuario
    """), {"pid": pid}).fetchall()
    
    for j in jugadores:
        print(f"  Equipo {j[1]}: {j[5]} (ID:{j[0]}) | rating: {j[2]} -> {j[3]} | delta: {j[4]}")
    
    print("\n=== HISTORIAL RATING DE ESTOS JUGADORES (este partido) ===")
    historial = db.execute(text("""
        SELECT hr.id_usuario, hr.rating_antes, hr.delta, hr.rating_despues,
               COALESCE(pu.nombre || ' ' || pu.apellido, u.nombre_usuario) as nombre
        FROM historial_rating hr
        JOIN usuarios u ON hr.id_usuario = u.id_usuario
        LEFT JOIN perfil_usuarios pu ON hr.id_usuario = pu.id_usuario
        WHERE hr.id_partido = :pid
        ORDER BY hr.id_usuario
    """), {"pid": pid}).fetchall()
    
    for h in historial:
        signo = "+" if h[2] > 0 else ""
        print(f"  {h[4]} (ID:{h[0]}): {h[1]} {signo}{h[2]} -> {h[3]}")
    
    print("\n=== RATING ACTUAL EN TABLA USUARIOS ===")
    for j in jugadores:
        rating = db.execute(text("SELECT rating, partidos_jugados FROM usuarios WHERE id_usuario = :uid"), {"uid": j[0]}).fetchone()
        print(f"  {j[5]} (ID:{j[0]}): rating={rating[0]}, partidos={rating[1]}")
else:
    print("  No se encontró partido para sala 7")

db.close()
