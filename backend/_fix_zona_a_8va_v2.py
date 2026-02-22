"""Corregir horarios Zona A 8va según lo pedido:
- Ocaña vs Palacio → vie 23:00, Cancha 5
- Palacio vs Palma → sáb 15:00, Cancha 5  
- Ocaña vs Palma → sáb 20:15, Cancha 5
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Parejas: Ocaña/Millicay=647, Palacio/Porras=655, Palma/Tapia=657

with engine.connect() as c:
    # P442: Ocaña(647) vs Palacio(655) -> vie 23:00 C5
    c.execute(text("""
        UPDATE partidos SET fecha_hora = '2026-02-20 23:00:00', fecha = '2026-02-20', cancha_id = 76
        WHERE id_partido = 442
    """))
    print("P442: Ocaña vs Palacio -> vie 20/02 23:00 Cancha 5 ✅")

    # P441: Palma(657) vs Palacio(655) -> sáb 15:00 C5
    c.execute(text("""
        UPDATE partidos SET fecha_hora = '2026-02-21 15:00:00', fecha = '2026-02-21', cancha_id = 76
        WHERE id_partido = 441
    """))
    print("P441: Palma vs Palacio -> sáb 21/02 15:00 Cancha 5 ✅")

    # P440: Palma(657) vs Ocaña(647) -> sáb 20:15 C5
    c.execute(text("""
        UPDATE partidos SET fecha_hora = '2026-02-21 20:15:00', fecha = '2026-02-21', cancha_id = 76
        WHERE id_partido = 440
    """))
    print("P440: Palma vs Ocaña -> sáb 21/02 20:15 Cancha 5 ✅")

    c.commit()

    # Verificar
    print("\n=== VERIFICACIÓN ZONA A 8va ===")
    rows = c.execute(text("""
        SELECT p.id_partido, p.fecha_hora, tc.nombre,
               p1n.nombre || ' ' || p1n.apellido || '/' || p2n.nombre || ' ' || p2n.apellido,
               p3n.nombre || ' ' || p3n.apellido || '/' || p4n.nombre || ' ' || p4n.apellido
        FROM partidos p
        JOIN torneo_canchas tc ON p.cancha_id = tc.id
        JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
        JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
        JOIN perfil_usuarios p2n ON tp1.jugador2_id = p2n.id_usuario
        JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
        JOIN perfil_usuarios p3n ON tp2.jugador1_id = p3n.id_usuario
        JOIN perfil_usuarios p4n ON tp2.jugador2_id = p4n.id_usuario
        WHERE p.zona_id = 202 ORDER BY p.fecha_hora
    """)).fetchall()
    for r in rows:
        fh = r[1].replace(tzinfo=None) if r[1].tzinfo else r[1]
        dia = fh.strftime('%a %d/%m %H:%M').replace('Fri','Vie').replace('Sat','Sáb').replace('Sun','Dom')
        print(f"  P{r[0]} | {dia} | {r[2]} | {r[3]} vs {r[4]}")
