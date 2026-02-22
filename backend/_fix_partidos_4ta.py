"""Corregir horarios de partidos 4ta torneo 38 según indicaciones:

Zona B (ID 198): Nieto Axel/Calderón (637) + Moreno/Nieto Camilo (641) + Ligorria/Brizuela (642)
  - 394: 637 vs 641 → viernes 20/02 18:00
  - 395: 637 vs 642 → sábado 21/02 15:00  
  - 396: 641 vs 642 → viernes 20/02 22:00

Zona C (ID 199): Olivera/Gurgone (635) + Bóveda/Verón (644) + Ferreyra/Gudiño (645)
  - 397: 635 vs 644 → viernes 20/02 19:40 (ya OK)
  - 398: 635 vs 645 → viernes 20/02 23:00
  - 399: 644 vs 645 → sábado 21/02 15:00

Zona E (ID 201): Rivero/Centeno (638) + Ocampo/Romero (643)
  - 403: 638 vs 643 → sábado 21/02 10:00
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

UPDATES = [
    # Zona B
    (394, "2026-02-20 18:00:00", "637 vs 641 → vie 18:00"),
    (396, "2026-02-20 22:00:00", "641 vs 642 → vie 22:00"),
    (395, "2026-02-21 15:00:00", "637 vs 642 → sáb 15:00"),
    # Zona C
    # 397 ya está OK (vie 19:40)
    (398, "2026-02-20 23:00:00", "635 vs 645 → vie 23:00"),
    (399, "2026-02-21 15:00:00", "644 vs 645 → sáb 15:00"),
    # Zona E
    (403, "2026-02-21 10:00:00", "638 vs 643 → sáb 10:00"),
]

try:
    for partido_id, nueva_fecha, desc in UPDATES:
        # Verificar antes
        antes = s.execute(text(
            "SELECT id_partido, pareja1_id, pareja2_id, fecha_hora FROM partidos WHERE id_partido = :pid"
        ), {"pid": partido_id}).fetchone()
        
        s.execute(text(
            "UPDATE partidos SET fecha_hora = :fh WHERE id_partido = :pid"
        ), {"pid": partido_id, "fh": nueva_fecha})
        
        print(f"✅ Partido {partido_id}: {desc} (antes: {antes[3]})")
    
    s.commit()
    
    # Verificar resultado final
    print("\n=== PARTIDOS 4ta ACTUALIZADOS ===")
    partidos = s.execute(text(
        "SELECT p.id_partido, p.pareja1_id, p.pareja2_id, p.fecha_hora, p.cancha_id, p.zona_id, "
        "z.nombre as zona_nombre "
        "FROM partidos p "
        "LEFT JOIN torneo_zonas z ON p.zona_id = z.id "
        "WHERE p.id_torneo = 38 AND p.categoria_id = 87 AND p.fase = 'zona' "
        "ORDER BY z.nombre, p.fecha_hora"
    )).fetchall()
    
    zona_actual = None
    for p in partidos:
        if p[6] != zona_actual:
            zona_actual = p[6]
            print(f"\n{zona_actual}:")
        print(f"  Partido {p[0]}: P{p[1]} vs P{p[2]} - {p[3]} cancha {p[4]}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback; traceback.print_exc()
    s.rollback()
finally:
    s.close()
