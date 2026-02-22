"""Inscribir Magali Ocaña (ID 237) + Joaquín Millicay (ID 79) en 8va torneo 38
Restricciones: vie 09-15, sáb 09-20, dom 09-15
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
s = Session()

TORNEO_ID = 38
CATEGORIA_ID = 89  # 8va
OCANA_ID = 237
MILLICAY_ID = 79

try:
    existe = s.execute(text("""
        SELECT id FROM torneos_parejas
        WHERE torneo_id = :t AND ((jugador1_id = :j1 AND jugador2_id = :j2)
            OR (jugador1_id = :j2 AND jugador2_id = :j1))
    """), {"t": TORNEO_ID, "j1": OCANA_ID, "j2": MILLICAY_ID}).fetchone()

    if existe:
        print(f"⚠️ Pareja ya existe (ID: {existe[0]})")
    else:
        restricciones = json.dumps([
            {"dias": ["viernes"], "horaInicio": "09:00", "horaFin": "15:00"},
            {"dias": ["sabado"], "horaInicio": "09:00", "horaFin": "20:00"},
            {"dias": ["domingo"], "horaInicio": "09:00", "horaFin": "15:00"}
        ])
        r = s.execute(text("""
            INSERT INTO torneos_parejas (torneo_id, categoria_id, jugador1_id, jugador2_id, estado, disponibilidad_horaria)
            VALUES (:t, :c, :j1, :j2, 'confirmada', CAST(:r AS jsonb)) RETURNING id
        """), {"t": TORNEO_ID, "c": CATEGORIA_ID, "j1": OCANA_ID, "j2": MILLICAY_ID, "r": restricciones})
        pid = r.fetchone()[0]
        s.commit()
        print(f"✅ Pareja {pid}: Ocaña Magali (ID {OCANA_ID}) + Millicay Joaquín (ID {MILLICAY_ID})")

    total = s.execute(text(
        "SELECT COUNT(*) FROM torneos_parejas WHERE torneo_id = :t AND categoria_id = :c"
    ), {"t": TORNEO_ID, "c": CATEGORIA_ID}).fetchone()[0]
    print(f"\nTotal parejas en 8va: {total}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback; traceback.print_exc()
    s.rollback()
finally:
    s.close()
