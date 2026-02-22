import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Parejas: Ocaña/Millicay=647, Palacio/Porras=655, Palma/Tapia=657
# Partidos actuales zona A:
#   P426: p1=647(Ocaña) vs p2=655(Palacio) - vie 15:00 -> cambiar a vie 23:00
#   P424: p1=657(Palma) vs p2=647(Ocaña) - sab 20:40 -> cambiar a Palacio vs Palma sab 15:00
#   P425: p1=657(Palma) vs p2=655(Palacio) - sab 23:59 -> cambiar a Ocaña vs Palma sab 20:15

with engine.connect() as c:
    # P426: Ocaña vs Palacio -> vie 23:00 (parejas ya correctas)
    c.execute(text("UPDATE partidos SET fecha_hora = '2026-02-20 23:00:00' WHERE id_partido = 426"))
    print("P426: Ocaña vs Palacio -> vie 23:00")

    # P424: actualmente Palma vs Ocaña -> cambiar a Palacio(655) vs Palma(657), sab 15:00
    c.execute(text("""
        UPDATE partidos SET pareja1_id = 655, pareja2_id = 657, fecha_hora = '2026-02-21 15:00:00'
        WHERE id_partido = 424
    """))
    print("P424: Palacio vs Palma -> sab 15:00")

    # P425: actualmente Palma vs Palacio -> cambiar a Ocaña(647) vs Palma(657), sab 20:15
    c.execute(text("""
        UPDATE partidos SET pareja1_id = 647, pareja2_id = 657, fecha_hora = '2026-02-21 20:15:00'
        WHERE id_partido = 425
    """))
    print("P425: Ocaña vs Palma -> sab 20:15")

    c.commit()

    # Verificar
    print("\nVerificación:")
    for pid in [426, 424, 425]:
        r = c.execute(text("""
            SELECT p.id_partido, p.fecha_hora, p.cancha_id, p.pareja1_id, p.pareja2_id,
                   p1n.nombre || ' ' || p1n.apellido, p2n.nombre || ' ' || p2n.apellido
            FROM partidos p
            JOIN torneos_parejas tp1 ON p.pareja1_id = tp1.id
            JOIN perfil_usuarios p1n ON tp1.jugador1_id = p1n.id_usuario
            JOIN torneos_parejas tp2 ON p.pareja2_id = tp2.id
            JOIN perfil_usuarios p2n ON tp2.jugador1_id = p2n.id_usuario
            WHERE p.id_partido = :pid
        """), {"pid": pid}).fetchone()
        print(f"  P{r[0]}: {r[5]}/{r[6]} | {r[1]} | cancha_id={r[2]}")
