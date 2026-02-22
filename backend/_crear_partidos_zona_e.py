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
    (658, 659, "2026-02-20 15:00:00", 76, "Calderón vs Martinez 15:00 C5"),
    (659, 648, "2026-02-20 18:00:00", 79, "Martinez vs Quiroz 18:00 C8"),
    (648, 658, "2026-02-20 21:00:00", 76, "Quiroz vs Calderón 21:00 C5"),
]

with engine.connect() as c:
    for p1, p2, fecha, cancha, desc in partidos:
        r = c.execute(text("""
            INSERT INTO partidos (id_torneo, categoria_id, pareja1_id, pareja2_id, fecha_hora, fecha, cancha_id, zona_id, estado, fase, origen, id_creador)
            VALUES (38, 88, :p1, :p2, :f, :d, :ch, 207, 'pendiente', 'grupos', 'manual', 2) RETURNING id_partido
        """), {"p1": p1, "p2": p2, "f": fecha, "d": "2026-02-20", "ch": cancha})
        pid = r.fetchone()[0]
        print(f"P{pid}: {desc}")
    c.commit()
    print("\n✅ 3 partidos creados en Zona E de 6ta")
