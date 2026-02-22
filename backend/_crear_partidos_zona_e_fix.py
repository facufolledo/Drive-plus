"""Crear 3 partidos de Zona E (6ta) - con fase='zona' corregido"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Zona E (ID 207) de 6ta (cat 88)
# Parejas: Calderón=658, Martinez=659, Quiroz=648
# Cancha 5=76, Cancha 8=79

partidos = [
    (658, 659, "2026-02-20 15:00:00", "2026-02-20", 76, "Calderón vs Martinez 15:00 C5"),
    (659, 648, "2026-02-20 18:00:00", "2026-02-20", 79, "Martinez vs Quiroz 18:00 C8"),
    (648, 658, "2026-02-20 21:00:00", "2026-02-20", 76, "Quiroz vs Calderón 21:00 C5"),
]

with engine.connect() as c:
    for p1, p2, fecha_hora, fecha, cancha, desc in partidos:
        r = c.execute(text("""
            INSERT INTO partidos (id_torneo, categoria_id, pareja1_id, pareja2_id, fecha_hora, fecha, cancha_id, zona_id, estado, fase, id_creador)
            VALUES (38, 88, :p1, :p2, :fh, :f, :ch, 207, 'pendiente', 'zona', 2) RETURNING id_partido
        """), {"p1": p1, "p2": p2, "fh": fecha_hora, "f": fecha, "ch": cancha})
        pid = r.fetchone()[0]
        print(f"  P{pid}: {desc}")
    c.commit()
    print("\n✅ 3 partidos creados en Zona E de 6ta")

    # Verificar
    print("\n=== VERIFICACIÓN ===")
    pts = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, p.cancha_id, 
               p1n.nombre || ' ' || p1n.apellido || '/' || p2n.nombre || ' ' || p2n.apellido,
               p3n.nombre || ' ' || p3n.apellido || '/' || p4n.nombre || ' ' || p4n.apellido
        FROM partidos p
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
        JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
        WHERE p.zona_id = 207
        ORDER BY p.fecha_hora
    """)).fetchall()
    for p in pts:
        fh = p[1].replace(tzinfo=None) if p[1].tzinfo else p[1]
        print(f"  P{p[0]} {fh.strftime('%a %d/%m %H:%M')} Cancha {p[2]} | {p[3]} vs {p[4]}")
